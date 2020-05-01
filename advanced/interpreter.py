# IMPORT
try:
    from pexpect import TIMEOUT, EOF, run
    from pexpect.popen_spawn import PopenSpawn
except ModuleNotFoundError:
    raise ModuleNotFoundError('Pexpect module is missing but required')
try:
    from requests import post
    from requests.exceptions import ConnectionError
except ModuleNotFoundError:
    raise ModuleNotFoundError('Requests module is missing but required')
try:
    import advanced.my_exceptions as MyExceptions
except ModuleNotFoundError:
    try:
        import my_exceptions as MyExceptions
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            'advanced/my_exceptions.py is missing, check the files are ' +
            'in place or download the repository again\n'
                )
from time import sleep
from shutil import copy
from os import listdir
from signal import SIGTERM

# PEXPECT COMMAND
mix_commands = {
        'deb0': 'wassabee mix --wallet:{} --keepalive',
        'deb1': 'wassabee mix --wallet:{} --destination:{} --keepalive',
        'source0': 'dotnet run --mix --wallet:{} --keepalive',
        'source1': 'dotnet run --mix --wallet:{} --destination:{} --keepalive',
        'targz0': './wassabee mix --wallet:{} --keepalive',
        'targz1': './wassabee mix --wallet:{} --destination:{} --keepalive',
            }
## RPC documentation link:
## https://docs.wasabiwallet.io/using-wasabi/RPC.html#wasabi-remote-procedure-call-interface

# WASABI INTERPRETER FUNCTIONS
def call_rpc(rpc_user, rpc_pwd, method):
    """
    Ask the RPC server for the given method and call the
    evaluate_response function.
    """
    base_url = 'http://127.0.0.1:37128/'
    try:
        response = post(base_url,
                        data=method,
                        auth=(rpc_user, rpc_pwd)
                        )
    except Exception as e:
        response = e
    return evaluate_response(response)

def evaluate_response(response):
    """
    Check the response and return either the result or raise an error.
    """
    if isinstance(response, Exception):
        raise type(response)(response)
    else:
        if response.status_code == 401:
            raise MyExceptions.WrongCredentials(
                                   'The RPC credentials in the ' +
                                   'settings.py file are incorrect\n' +
                                   'Fix it and try again'
                                    )
        try:
            error = response.json()['error']
        except (ValueError, KeyError):
            try:
                return response.json()['result']
            except (ValueError, KeyError):
                return
        else:
            raise MyExceptions.RpcError(error['message'])

def is_wasabi_running():
    """
    Look for Wasabi process id.
    """
    wasabi_process_id = run('pidof wassabee')
    if wasabi_process_id:
        return True
    else:
        return False

def launch_wasabi(rpc_user, rpc_pwd, path, pwd='',
                  name='placeholder', destination='', launch_path = ''):
    """
    Launch Wasabi deamon and return pexpect child.
    """
    # If no launch_path provided, assume deb package is installed.
    if not launch_path:
        if name == 'placeholder':
            command = mix_commands['deb0'].format(name)
            if 'placeholder.json' not in listdir(path+'Wallets'):
                copy('advanced/placeholder.json', path+'Wallets')
        elif name == 'spawned':
            command = mix_commands['deb1'].format(name, destination)
    else:
        # If launch_path is provided, if WalletWasabi.Gui in it,
        # assume source code.
        if 'WalletWasabi.Gui' in launch_path:
            if name == 'placeholder':
                command = mix_commands['source0'].format(name)
                if 'placeholder.json' not in listdir(path+'Wallets'):
                    copy('advanced/placeholder.json', path+'Wallets')
            elif name == 'spawned':
                command = mix_commands['source1'].format(name, destination)
        # If launch_path is provided, if WalletWasabi.Gui not in it,
        # assume targz.
        else:
            if name == 'placeholder':
                command = mix_commands['targz0'].format(name)
                if 'placeholder.json' not in listdir(path+'Wallets'):
                    copy('advanced/placeholder.json', path+'Wallets')
            elif name == 'spawned':
                command = mix_commands['targz1'].format(name, destination)
    print('Starting Wasabi')
    if launch_path:
        try:
            wasabi_proc = PopenSpawn(command, cwd=launch_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(str(e) + ', check that your ' +
                            '"launch_path" setting is correct')
    else:
        wasabi_proc = PopenSpawn(command)
    index = wasabi_proc.expect_exact(['Password:',
                                      'selected wallet does not exist',
                                      TIMEOUT,
                                      EOF
                                      ], timeout=30)
    if index == 0:
        wasabi_proc.sendline(pwd)
    elif index == 1:
        raise MyExceptions.WalletMissing(name +
                                    '.json wallet does not exist')
    elif index == 2:
        raise MyExceptions.ProcessTimeout('Wasabi process TIMEOUT')
    elif index == 3:
        raise EOFError('Pexpect EOF')
    index = wasabi_proc.expect_exact(['Correct password',
                                      'Wrong password',
                                      TIMEOUT,
                                      EOF
                                      ], timeout=30)
    if index == 0:
        print('Wasabi daemon started')
    if index == 1:
        raise MyExceptions.WrongPassword('Wrong password')
    if index == 2:
        raise MyExceptions.ProcessTimeout('Wasabi process TIMEOUT')
    if index == 3:
        raise EOFError('Pexpect EOF')
    index = wasabi_proc.expect_exact(['Starting Wallet',
                                      TIMEOUT,
                                      EOF
                                      ], timeout=30)
    if index == 0:
        print('Wallet starting')
    if index == 1:
        raise MyExceptions.ProcessTimeout('Wasabi process TIMEOUT')
    if index == 2:
        raise EOFError('Pexpect EOF')
    if is_wasabi_running():
        print('Wasabi started')
    else:
        raise MyException.FailedLaunch('Wasabi has not started, try again')
    return wasabi_proc

def generate_wallet(rpc_user, rpc_pwd, pwd, name='spawned'):
    """
    Generate Wasabi wallet with given password and show seed.
    """
    data = ('{"jsonrpc":"2.0","id":"1","method":"createwallet",' +
           '"params":["WalletName", "Password"]}'.replace(
                                                'WalletName', name))
    data = data.replace('Password', pwd)
    return call_rpc(rpc_user, rpc_pwd, data)

def select_wallet(rpc_user, rpc_pwd, name='spawned'):
    """
    Allow the RPC server to open/switch wallets.
    Return nothing.
    """
    print('\nLoading...')
    # Tries to select the wallet until no more 'no wallet selected'
    # RpcError.
    # This should be improved.
    while True:
        data = ('{"jsonrpc":"2.0","method":"selectwallet",' +
               '"params" : ["WalletName"]}'.replace('WalletName', name))
        call_rpc(rpc_user, rpc_pwd, data)
        try:
            selected_wallet = get_wallet_info(rpc_user,
                                              rpc_pwd,
                                              )
        except MyExceptions.RpcError:
            sleep(1)
            continue
        else:
            # Checks the correct wallet has indeed been selected.
            if selected_wallet['walletName'] != name:
                raise MyExceptions.WrongSelection(
                                   '{}.json wallet has not been ' +
                                   'selected, try again'.format(name)
                                   )
            break
    return

def get_wallet_info(rpc_user, rpc_pwd):
    """
    Return info about the selected wallet.
    """
    data = '{"jsonrpc":"2.0","id":"1","method":"getwalletinfo"}'
    return call_rpc(rpc_user, rpc_pwd, data)

def generate_address(rpc_user, rpc_pwd, observer):
    """
    Generate an unused receiving address.
    """
    data = ('{"jsonrpc":"2.0","id":"1","method":"getnewaddress",' +
           '"params":["Observer"]}'.replace('Observer', observer))
    return call_rpc(rpc_user, rpc_pwd, data)

def stop_wasabi(rpc_user, rpc_pwd, wasabi_proc):
    """
    Stop and exit Wasabi.
    Return nothing.
    """
    data = '{"jsonrpc":"2.0", "method":"stop"}'
    print('Stopping Wasabi')
    call_rpc(rpc_user, rpc_pwd, data)
    # Checks the Wasabi process indeed quit.
    index = wasabi_proc.expect_exact(['Daemon stopped',
                                      EOF,
                                      ], timeout=None)
    if index == 0:
        wasabi_proc.kill(SIGTERM)
        wasabi_proc.wait()
        print('Stopped')
        return
    elif index == 1:
        raise EOFError

def get_wasabi_status(rpc_user, rpc_pwd):
    """
    Return information useful to understand the Wasabi's status.
    """
    data = '{"jsonrpc":"2.0","id":"1","method":"getstatus"}'
    return call_rpc(rpc_user, rpc_pwd, data)

def get_list_keys(rpc_user, rpc_pwd):
    """
    Return the list of all the generated keys.
    """
    data = '{"jsonrpc":"2.0","id":"1","method":"listkeys"}'
    return call_rpc(rpc_user, rpc_pwd, data)

def get_wallet_utxos(rpc_user, rpc_pwd):
    """
    Return the list of confirmed and unconfirmed coins that are unspent.
    """
    data = '{"jsonrpc":"2.0","id":"1","method":"listunspentcoins"}'
    return call_rpc(rpc_user, rpc_pwd, data)
