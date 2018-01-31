"""
Adapted from:
https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto
"""
import os
import sys
import random
import struct
import hashlib
import argparse
try:
    from Crypto.Cipher import AES
except ImportError:
    print("error: run `pip install pycrypto` before running vault")
    sys.exit(1)

vault_header = 'vault/encrypted'


def encrypt_file(key, infile, outfile=None, chunksize=64*1024):
    iv = ''.join(str(random.randint(0, 9)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(infile)

    with open(infile, 'rb') as file:
        header = file.readline()
        if header.decode('utf-8').strip() == vault_header:
            raise RuntimeError('this file is already encrypted by vault')

    with open(infile, 'rb') as file:
        contents = f'{vault_header}\n'.encode('utf-8')  # add vault header
        contents += struct.pack('<Q', filesize)
        contents += iv.encode('utf-8')

        while True:
            chunk = file.read(chunksize)
            if len(chunk) == 0:
                break
            elif len(chunk) % 16 != 0:
                padding = ' ' * (16 - len(chunk) % 16)
                chunk += padding.encode('utf-8')

            contents += encryptor.encrypt(chunk)

    if not outfile:
        outfile = infile

    with open(outfile, 'wb') as file:
        file.write(contents)


def decrypt_file(key, infile, outfile=None, chunksize=24*1024):
    with open(infile, 'rb') as file:
        header = file.readline()
        if header.decode('utf-8').strip() != vault_header:
            raise RuntimeError('this file is not encrypted by vault')

        origsize = struct.unpack('<Q', file.read(struct.calcsize('Q')))[0]
        iv = file.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        contents = ''.encode('utf-8')
        while True:
            chunk = file.read(chunksize)
            if len(chunk) == 0:
                break
            contents += decryptor.decrypt(chunk)

    if not outfile:
        outfile = infile

    with open(outfile, 'wb') as file:
        file.write(contents)
        file.truncate(origsize)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password_file', default='.vault-password')
    parser.add_argument('-i', '--infile', required=True)
    parser.add_argument('-o', '--outfile', default=None)
    parser.add_argument('-e', '--encrypt', action='store_true', default=False)

    args = parser.parse_args()
    with open(args.password_file, 'r') as file:
        password = file.readline().strip()
    key = hashlib.sha256(password.encode('utf-8')).digest()

    if args.encrypt:
        f = encrypt_file
    else:
        f = decrypt_file
    f(key, args.infile, args.outfile)
