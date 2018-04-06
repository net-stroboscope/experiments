#!/bin/python2
import argparse
import socket
import random
import time
import struct


# Packet rate per flow
PKT_SEC = 100


def _build_parser():
    parser = argparse.ArgumentParser(description="Start a traffic source")
    parser.add_argument('--dst', default=None, required=True,
                        help='The destination address to target')
    parser.add_argument('--origin', default=None, required=True,
                        help='The source address to use')
    parser.add_argument('--count', default=None, required=True,
                        help='The number of flows to spawn')
    return parser


def _parse_args(parser):
    return parser.parse_args()


def _main():
    args = _parse_args(_build_parser())
    sfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sfd.bind((args.origin, 12345))
    # pick dst ports
    dests = [(args.dst, p)
             for p in random.sample(list(xrange(1025, 65535)), int(args.count))]
    dst = args.dst
    sqc = 0
    while True:
        # same payload across flows
        payload = struct.pack('>Q', sqc)
        # flood the dest
        for dst in dests:
            try:
                sfd.sendto(payload, 0, dst)
            except (IOError, OSError, socket.error):
                pass
        sqc += 1
        # wait until the next flooding session
        time.sleep(1 / PKT_SEC)


if __name__ == '__main__':
    _main()
