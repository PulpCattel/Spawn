## The descriptor checksum functions are taken from Andrew Chow's repository
## Thanks Andrew <3
## https://github.com/achow101/output-descriptors

def PolyMod(c, val):
    c0 = c >> 35
    c = ((c & 0x7ffffffff) << 5) ^ val
    if (c0 & 1):
        c ^= 0xf5dee51989
    if (c0 & 2):
        c ^= 0xa9fdca3312
    if (c0 & 4):
        c ^= 0x1bab10e32d
    if (c0 & 8):
        c ^= 0x3706b1677a
    if (c0 & 16):
        c ^= 0x644d626ffd
    return c

def DescriptorChecksum(desc):
    INPUT_CHARSET = "0123456789()[],'/*abcdefgh@:$%{}IJKLMNOPQRSTUVWXYZ&+-.;<=>?!^_|~ijklmnopqrstuvwxyzABCDEFGH`#\"\\ ";
    CHECKSUM_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";

    c = 1
    cls = 0
    clscount = 0
    for ch in desc:
        pos = INPUT_CHARSET.find(ch)
        if pos == -1:
            return ""
        c = PolyMod(c, pos & 31)
        cls = cls * 3 + (pos >> 5)
        clscount += 1
        if clscount == 3:
            c = PolyMod(c, cls)
            cls = 0
            clscount = 0
    if clscount > 0:
        c = PolyMod(c, cls)
    for j in range (0, 8):
        c = PolyMod(c, 0)
    c ^= 1

    ret = [None] * 8
    for j in range(0, 8):
        ret[j] = CHECKSUM_CHARSET[(c >> (5 * (7 - j))) & 31]
    return ''.join(ret)

def AddChecksum(desc):
    return desc + "#" + DescriptorChecksum(desc)

def build_command(xpub, fingerprint):
    """
    Create import multi command
    """
    command = 'importmulti '
    template = (
        '[{{"range": [0, 1000], "timestamp": "now", "keypool": true, '
        '"watchonly": true, "desc": "{}", "internal": false}}, '
        '{{"range": [0, 1000], "timestamp": "now", "keypool": true, '
        '"watchonly": true, "desc": "{}", "internal": true}}]'
                )
    desc0 = AddChecksum('wpkh([{}/84h/0h/0h]{}/0/*)'.format(fingerprint, xpub))
    desc1 = AddChecksum('wpkh([{}/84h/0h/0h]{}/1/*)'.format(fingerprint, xpub))
    template = template.format(desc0, desc1)
    return command + "'" + template + "'"

if __name__ == '__main__':
    xpub = input('Xpub: ')
    fingerprint = input('Fingerprint: ')
    print('\nUse the following command to import your wallet as ' +
          'a watch-only in BitcoinCore. Look at the README.md file ' +
          'for more info\n\n'
          )
    print(build_command(xpub, fingerprint))
