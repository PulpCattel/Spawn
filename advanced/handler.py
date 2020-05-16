## IMPORTS
try:
    import advanced.interpreter
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        'advanced/interpreter.py is missing, check the files are ' +
        'in place or download the repository again\n'
            )
try:
    import advanced.my_exceptions as MyExceptions
except ModuleNotFoundError:
    raise ModuleNotFoundError(
          'advanced/my_exceptions.py is missing, check the files are ' +
          'in place or download the repository again\n'
            )
try:
    import advanced.watch_only
except ModuleNotFoundError:
    raise ModuleNotFoundError(
              'advanced/watch_only.py is missing, check the files are ' +
              'in place or download the repository again\n'
                )
from requests import get
from shutil import copy
from time import sleep
from getpass import getpass
from secrets import choice
from string import ascii_letters, digits
from subprocess import run
from os import listdir, getcwd
from pathlib import Path

# HANDLER
class Handler():
    """
    Factotum.
    """
    def __init__(self, settings):
        """
        Initialize the Handler with the settings and check script status
        looking for spawned.json in Wasabi directory.
        """
        self.wasabi_path = str(Path.home())+'/.walletwasabi/client/'
        try:
            self.launch_path = settings['launch_path']
            self.auto_generate = settings['auto_generate']
            self.auto_backup = settings['auto_backup']
            self.watch_only = settings['watch_only']
            self.RpcUser = settings['JsonRpcUser']
            self.RpcPassword = settings['JsonRpcPassword']
            self.observer = settings['observer']
            self.num_addresses = settings['num_addresses']
            self.destination = settings['destination']
        except(KeyError):
            raise KeyError(
                  'settings.py is messed up, check the settings are ' +
                  'okay or download the repository again\n'
                   )
        self.check_settings()
        try:
            with open(self.wasabi_path+'Config.json') as config:
                config_file = config.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                    '"Config.json" file is missing, if this ' +
                    'is the first Wasabi run, you have to ' +
                    'launch it manually.\n This operation has ' +
                    'to be done just once as long as ".walletwasabi" ' +
                    'folder is not removed'
                            )
        if '"JsonRpcServerEnabled": false' in config_file:
            raise MyExceptions.RpcDisabled(
                'RPC server is not enabled, turn it on ' +
                'changing "JsonRpcServerEnabled" to true in the ' +
                'Wasabi config.json file'
                    )
        elif '"JsonRpcServerEnabled"' not in config_file:
            raise MyExceptions.RpcDisabled(
                'RPC configuration is missing from the "config.json" ' +
                'file, are you using Wasabi version 1.1.11+?'
                    )
        # If spawned wallet already there we can skip all the wallet
        # and password creation
        if 'spawned.json' in listdir(self.wasabi_path+'Wallets'):
            self.status = 'mixing'
        else:
            self.status = 'first_run'
        if advanced.interpreter.is_wasabi_running():
            raise MyExceptions.AlreadyRunning(
                        'Wasabi is currently running, shut it down ' +
                        'and launch spawn.py again'
                                )

    def clear(self):
        """
        Clear terminal.
        """
        run(['tput', 'reset'])

    def check_settings(self):
        """
        Some quick sanity check of the user settings.
        """
        if type(self.launch_path) is not str:
            raise TypeError('"launc_path" setting has to be a string')
        if type(self.auto_generate) is not bool:
            raise TypeError('"auto_generate" setting has to be True or False')
        if type(self.auto_backup) is not bool:
            raise TypeError('"auto_backup" setting has to be True or False')
        if type(self.watch_only) is not bool:
            raise TypeError('"watch_only" setting has to be True or False')
        if type(self.RpcUser) is not str:
            raise TypeError('"JsonRpcUser" setting has to be a string')
        if type(self.RpcPassword) is not str:
            raise TypeError('"JsonRpcPassword" setting has to be a string')
        if type(self.observer) is not str:
            raise TypeError('"observer" setting has to be a string')
        if type(self.num_addresses) is not int:
            raise TypeError('"num_addresses" setting has to be a integer')
        if type(self.destination) is not str:
            raise TypeError('"destination" setting has to be a string')
        if not self.observer:
            raise ValueError('"observer" setting cannot be empty')
        if self.num_addresses > 20:
            raise ValueError('"num_addresses" setting can be max 20, ' +
                             'if you need more addresses just use ' +
                             'another spawned wallet'
                             )
        if self.num_addresses < 1:
            raise ValueError('"num_addresses" setting cannot be 0 or ' +
                             'negative'
                             )
        if not self.destination:
            raise ValueError('"destination" setting cannot be empty')
        if '{}.json'.format(self.destination) not in listdir(
                                    self.wasabi_path+'Wallets'):
            raise MyExceptions.WalletMissing(
                                'destination wallet not found')
        return

    def create_password(self):
        """
        Create random password for the wallet.
        This encrypts the secret and acts as a 13th word.
        """
        pool = ascii_letters + digits
        pwd = ''.join(choice(pool) for i in range(25))
        try:
            input('\nPassword autogeneration is set to True\n' +
                'This is your random generated password:\n' +
                pwd +
                '\n\nThis encrypts your secret and acts as a 13th word'
                "\n\nIt's not stored anywhere, so you have to save it,"
                ' if you lose your password you could lose your bitcoin!\n'
                '\nPress enter to continue\n'
                    )
        except:
            pass
        self.clear()
        while True:
            try:
                chk_pwd = getpass('Repeat Wallet Password: ')
            except:
                print('Invalid password')
                continue
            if pwd == chk_pwd:
                self.pwd = pwd
                break
            else:
                print('Passwords do not match, try again')
        return

    def user_password(self):
        """
        Ask the user for the wallet password.
        This encrypts the secret and acts as a 13th word.
        """
        print('\nPassword autogeneration is set to false\n' +
          'Please provide your password,' +
          ' this encrypts your secret and acts as a 13th word' +
          "\n\nIt's not stored anywhere, so you have to save it," +
          ' if you lose your password you cannot spend your bitcoin!\n' +
          '\nPassword is not shown, you have to type it blind'
                )
        # Keeps asking until user insert 2 times the same password
        while True:
            try:
                pwd = getpass('Wallet Password (max 150 char): \n')
            except:
                print('Invalid password')
                continue
            if len(pwd) > 150:
                print('Password too long')
                continue
            try:
                chk_pwd = getpass('\nRepeat Wallet Password: \n')
            except:
                print('Invalid password')
                continue
            if pwd == chk_pwd:
                self.pwd = pwd
                break
            else:
                print('Passwords do not match, try again\n')
        return

    def create_wallet(self):
        """
        Launch wasabi, generate wallet and select it.
        """
        self.clear()
        if advanced.interpreter.is_wasabi_running():
            raise MyExceptions.AlreadyRunning(
                        'Wasabi is currently running, shut it down ' +
                        'and launch spawn.py again'
                        )
        self.wassabee = advanced.interpreter.launch_wasabi(
                                    self.wasabi_path,
                                    launch_path = self.launch_path,
                                           )
        wallet = advanced.interpreter.generate_wallet(self.RpcUser,
                                                      self.RpcPassword,
                                                      self.pwd)
        self.clear()
        print('Recovery words:\n{}'.format(wallet) +
              '\n\nThey are encrypted by Wasabi in the '
              'spawned.json wallet file'
              '\nBackup either the words list or the wallet file!'
              )
        self.choose_wallet()
        return

    def create_watch_only(self, path):
        """
        Create Bitcoin Core watch-only to import with import multi.
        The command is saved in the core_watch_only.txt file
        """
        wallet_info = advanced.interpreter.get_wallet_info(
                                             self.RpcUser,
                                             self.RpcPassword,
                                            )
        command = advanced.watch_only.build_command(
                                wallet_info['extendedAccountPublicKey'],
                                wallet_info['masterKeyFingerprint'],
                                    )
        with open(path+'/user_data/core_watch_only.txt', 'w') as core_file:
            core_file.write('Use this command to import your wallet as ' +
                            'watch-only in Bitcoin Core. Look at the ' +
                            'README.md file for more info'
                            )
            core_file.write('\n\n' + command)
        return

    def choose_wallet(self):
        """
        Select a wallet.
        """
        advanced.interpreter.select_wallet(self.RpcUser,
                                           self.RpcPassword
                                            )
        return

    def create_addresses(self):
        """
        Create user defined number of addresses, 10 by default.
        """
        self.addresses = []
        print('\nReceiving addresses:')
        for i in range(self.num_addresses):
            self.addresses.append(
                                advanced.interpreter.generate_address(
                                                    self.RpcUser,
                                                    self.RpcPassword,
                                                    self.observer
                                                    ))
            print(self.addresses[-1]['address'])
        try:
            input('\nThese are your receiving addresses, you can ' +
                  'deposit to any of them and mixing will start ' +
                  'automatically.\nThe same list is also saved in ' +
                  'the "receiving_addresses.txt" file, alongside ' +
                  'their keypath and public key.' +
                  '\nPress enter to continue'
                  )
        except:
            pass
        return

    def make_backup(self, path, name='spawned'):
        """
        Copy the name.json wallet file into the Spawn folder.
        """
        wallet_name = name + '.json'
        path_from = self.wasabi_path+'Wallets/{}'.format(wallet_name)
        copy(path_from, path+'/user_data/'+wallet_name)
        return

    def stamp_addresses(self, path):
        """
        Dump addresses list in receiving_addresses.txt alongside
        key path and public key.
        """
        with open(path+'/user_data/receiving_addresses.txt', 'w') as addresses_file:
            for address in self.addresses:
                addresses_file.write(address['address'])
                addresses_file.write('\n\t'+address['keyPath']+'\n')
                addresses_file.write('\t'+address['publicKey']+'\n')
        return

    def close_wasabi(self):
        """
        Shutdown Wasabi daemon.
        """
        advanced.interpreter.stop_wasabi(self.RpcUser,
                                         self.RpcPassword,
                                         self.wassabee,
                                         )
        return

    def ask_password(self):
        """
        Ask user for already generated password.
        """
        # Keeps asking until user insert 2 times the same password
        while True:
            try:
                pwd = getpass('Wallet Password: \n')
            except:
                print('Invalid password')
                continue
            if len(pwd) > 150:
                print('Password too long')
                continue
            try:
                chk_pwd = getpass('\nRepeat Wallet Password: \n')
            except:
                print('Invalid password')
                continue
            if pwd == chk_pwd:
                self.pwd = pwd
                break
            else:
                print('Passwords do not match, try again\n')
        return

    def start_mixing(self):
        """
        Launch Wasabi daemon with spawned wallet and select it.
        """
        self.clear()
        # Wasabi should never be running at this point
        # but better safe than sorry
        if advanced.interpreter.is_wasabi_running():
            raise MyExceptions.AlreadyRunning(
                        'Wasabi is currently running, shut it down ' +
                        'and launch spawn.py again'
                        )
        self.wassabee = advanced.interpreter.launch_wasabi(
                                           self.wasabi_path,
                                           self.pwd,
                                           'spawned',
                                           self.destination,
                                           self.launch_path,
                                           )
        self.choose_wallet()
        del self.pwd
        return

    def print_ui(self):
        """
        Print the mixing UI, it's refreshed randomly between
        2 and 7 seconds.
        """
        try:
            while True:
                wasabi_status = advanced.interpreter.get_wasabi_status(
                                                self.RpcUser,
                                                self.RpcPassword,
                                                            )
                wallet_info = advanced.interpreter.get_wallet_info(
                                                self.RpcUser,
                                                self.RpcPassword,
                                                            )
                utxos = advanced.interpreter.get_wallet_utxos(
                                                self.RpcUser,
                                                self.RpcPassword,
                                                            )
                unused_addresses = self.find_unused()
                if wasabi_status['network'] == 'Main':
                    cj_info = self.find_cj_info(True)
                else:
                    cj_info = self.find_cj_info()
                self.clear()
                print('Wasabi status:')
                print('\tNetwork: {}'.format(wasabi_status['network']))
                print('\tTor: {}'.format(wasabi_status['torStatus']))
                print('\tBackend: {}'.format(wasabi_status['backendStatus']))
                if wasabi_status['filtersLeft'] == 0:
                    print('\tFilters: up to date')
                else:
                    print('\tFilters: {} filters left'.format(
                                            wasabi_status['filtersLeft']))
                print('\tPeers: {}'.format(len(wasabi_status['peers'])))
                print('\tBTC/USD: {}'.format(wasabi_status['exchangeRate']))
                print('\nWallet: {}'.format(wallet_info['walletFile']))
                print('\n\tBalance: {:f}'.format(wallet_info['balance']/10**8))
                print('\nDestination wallet: {}'.format(self.destination))
                print('\nUnused addresses:')
                # The return of find_unused() can be a string if
                # receiving_addresses.txt is missing
                if type(unused_addresses) is str:
                    print(unused_addresses)
                else:
                    for address in unused_addresses:
                        print('\t{}'.format(address))
                print('\nUTXOs:')
                for utxo in utxos:
                    print('\tTxid: {}'.format(utxo['txid']))
                    print('\t\tAddress: {}'.format(utxo['address']))
                    print('\t\tObserver: {}'.format(utxo['label']))
                    print('\t\tConfirmed: {}'.format(utxo['confirmed']))
                    print('\t\tAmount: {:f}'.format(utxo['amount']/10**8))
                    print('\t\tAnonymity Set: {}'.format(utxo['anonymitySet']))
                    print('\t\tKeypath: {}'.format(utxo['keyPath']))
                print('\nCoinJoin status:')
                try:
                    print('\tPhase: {}'.format(cj_info['phase']))
                    print('\tDenomination: {}'.format(
                                cj_info['denomination']))
                    print('\tRegistration ends at: {}'.format(
                                cj_info['inputRegistrationTimesout']))
                    print('\tPeers registered: {}'.format(
                                cj_info['registeredPeerCount']))
                    print('\tCoordinator fee % per AS: {}'.format(
                                cj_info['coordinatorFeePercent']))
                except (TypeError, KeyError) as e:
                    print(cj_info)
                print('\nPress ctrl+c to quit')
                sleep(choice(range(2, 7+1)))
        except KeyboardInterrupt:
            self.clear()
            self.close_wasabi()
        return

    def find_unused(self):
        """
        Return list of  generated unused addresses from
        receiving_addresses.txt and check vs utxo list to find used one.
        Then add '(USED)' in front of the used addresses and remove them
        from UI.
        """
        if 'receiving_addresses.txt' not in listdir(getcwd()+'/user_data'):
            return ('"receiving_addresses.txt" is missing, unable to ' +
                    'show unused addresses'
                    )
        unused_addresses = []
        generated_addresses = []
        used_addresses = []
        counter = 0
        is_changed = False
        wallet_utxos = advanced.interpreter.get_wallet_utxos(
                                                self.RpcUser,
                                                self.RpcPassword,
                                                    )
        utxo_addresses = [utxo['address'] for utxo in wallet_utxos]

        with open(getcwd()+'/user_data/receiving_addresses.txt') as addresses_file:
            lines = addresses_file.readlines()
        for line in lines:
            if line.strip()[:3] == 'tb1' or line.strip()[:3] == 'bc1':
                if line.strip() in utxo_addresses:
                    lines[counter] = '(USED) '+line
                    is_changed = True
                else:
                    unused_addresses.append(line.strip())
            counter += 1
        if is_changed:
            with open(getcwd()+'/user_data/receiving_addresses.txt',
                                                'w') as addresses_file:
                for line in lines:
                    addresses_file.write(line)
        return unused_addresses

    def find_cj_info(self, main=False):
        """
        Fetch Wasabi onion V3 backend for CoinJoin information
        If Tor is not running, or other problems, return an
        explanation and the error.
        """
        if main:
            url = (
                'http://wasabiukrxmkdgve5kynjztuovbg43uxcbcxn6y2okcrsg' +
                '7gb6jdmbad.onion/api/v3/btc/ChaumianCoinJoin/states'
                )
        else:
            url = (
                'http://testwnp3fugjln6vh5vpj7mvq3lkqqwjj3c2aa' +
                'fyu7laxz42kgwh2rad.onion/api/v3/btc/' +
                'ChaumianCoinJoin/states'
                )
        proxies = {'http': 'socks5h://127.0.0.1:9050',
                   'https': 'socks5h://127.0.0.1:9050',
                   }
        try:
            response = get(url, proxies=proxies)
        except Exception as e:
            return ('Unable to fetch backend V3 onion site:\n' +
                    e.__repr__())
        else:
            return response.json()[0]
