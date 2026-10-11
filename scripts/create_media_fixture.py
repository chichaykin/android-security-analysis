#!/usr/bin/env python3
"""Create a deterministic 256x256 synthetic PNG for isolated gallery tests."""
import argparse
import hashlib
import pathlib
import struct
import zlib

def fixture():
    raw = b''.join(b'\x00' + bytes([32, 120, 200]) * 256 for _ in range(256))
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 256, 256, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists')
    data = fixture()
    args.output.write_bytes(data)
    print(hashlib.sha256(data).hexdigest())

if __name__ == '__main__':
    main()
