#!/usr/bin/env python

import sys
import logging

from davies import compass

logging.basicConfig(level=logging.DEBUG)


def makparser(makfile):
	compass.CompassProjectParser(makfile).parse()


if __name__ == '__main__':
	makparser(sys.argv[1])
