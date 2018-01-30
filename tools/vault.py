"""
Adapted from:
https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto
"""
import os
import random
import struct
import hashlib
import argparse
try:
    from Crypto.Cipher import AES
except ImportError:
    print('run `pip install pycrypto` before running vault')


def encrypt_file(key, infile, outfile=None, chunksize=64*1024):
    iv = ''.join(str(random.randint(0, 9)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(infile)

    with open(infile, 'rb') as file:
        contents = 'encrypted\n'.encode('utf-8')  # add 'encrypted' header
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
        file.readline()  # ignore 'encrypted' header

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
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-i', '--infile', required=True)
    parser.add_argument('-o', '--outfile', default=None)
    parser.add_argument('-e', '--encrypt', action='store_true', default=False)

    args = parser.parse_args()
    key = hashlib.sha256(args.password.encode('utf-8')).digest()

    if args.encrypt:
        f = encrypt_file
    else:
        f = decrypt_file
    f(key, args.infile, args.outfile)