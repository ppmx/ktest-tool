#!/usr/bin/env python3

import os
import struct

class KleeTestError(Exception):
    pass

class KleeTest:
    version = 3

    @staticmethod
    def from_file(path):

        # TODO: include this reader. actually it may raise some unhandled
        # exceptions if the given test file is not in right format
        def sread(fd, n):
            b = fd.read(n)
            if len(b) != n:
                raise KleeTestError
            return b

        # if the requested file cant be found:
        if not os.path.exists(path):
            raise KleeTestError('requested file not found')

        # open and process file:
        with open(path, 'rb') as f:
            # check magic number:
            if f.read(5) not in [b'KTEST', b'BOUT\n']:
                raise KleeTestError('invalid file')

            # check test version:
            version = struct.unpack('>i', f.read(4))[0]
            if version > KleeTest.version:
                raise KleeTestError('unrecognized version')

            # parse argument section:
            num_args, args = struct.unpack('>i', f.read(4))[0], []
            for _ in range(num_args):
                size = struct.unpack('>i', f.read(4))[0]
                # TODO: decode(encode(x)) == x..
                args.append(str(f.read(size).decode(encoding='ascii')))

            # parse symbolic argument section:
            symArgvs = struct.unpack('>i', f.read(4))[0] if version >= 2 else 0
            symArgvLen = struct.unpack('>i', f.read(4))[0] if version >= 2 else 0

            # parse object section:
            objects, num_objects = [], struct.unpack('>i', f.read(4))[0]
            for _ in range(num_objects):
                name = f.read(struct.unpack('>i', f.read(4))[0])
                obj = f.read(struct.unpack('>i', f.read(4))[0])
                objects.append((name, obj))

            return KleeTest(version, args, symArgvs, symArgvLen, objects, path)

    def __init__(self, version, args, symArgvs, symArgvLen, objects, filename=None):
        """
        Excepted parameters:

            version:    integer
            args:       list of strings
            symArgvs:   bytes object
            symArgvLen: integer
            objects:    list of bytes objects
        """
        self.version = version
        self.args = args
        self.symArgvs = symArgvs
        self.symArgvLen = symArgvLen
        self.objects = objects
        self.filename = filename

def trim_zeros(data):
    for i in range(0, len(data), -1):
        if data[i] != '\x00':
            return data[:i+1]
    return ''

def main(argv):
    from optparse import OptionParser

    op = OptionParser('Usage: %prog [options] files')

    op.add_option('', '--trim-zeros', action='store_true', help='trim tailing zeros')
    op.add_option('', '--write-ints', action='store_true', help='convert words to integers')

    opts, args = op.parse_args()

    if len(args) == 0:
        op.error('need at least one file')

    for testfile in args:
        b = KleeTest.from_file(testfile)
        print('[+] klee test file:', b.filename)
        print('version:', b.version)
        print('arguments:', b.args)
        print('number objects:', len(b.objects))

        for i, (name, data) in enumerate(b.objects):
            s = trim_zeros(data) if opts.trim_zeros else data
            payload = struct.unpack('>i', s)[0] if opts.write_ints and len(data) == 4 else s

            print("[Object {0:2d}] name: {1}".format(i, name))
            print("[Object {0:2d}] size: {1}".format(i, len(data)))
            print("[Object {0:2d}] data: {1}".format(i, payload))

if __name__ == '__main__':
    from sys import argv
    main(argv)

