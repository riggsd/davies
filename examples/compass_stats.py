#!/usr/bin/env python
"""
Print a list of survey participants with their total feet surveyed.

usage: compass_stats.py DATFILE...


Example:

$ ./examples/compass_stats.py caves/*.dat
Rick R:   100262.7
Scott W:   50677.9
Peter P:   49401.7
Bob An:    47950.6
John H:    40586.3
Bob Al:    35925.8
Ralph H:   33693.5
Miles D:   32673.2
Stevan B:  31508.3
Aaron M:   27521.8
...

"""

import sys
import logging

from davies import compass


def compass_stats(datfiles):
    stats = {}

    for datfile in datfiles:
        for survey in compass.DatFile.read(datfile):
            for name in survey.team:
                stats[name] = stats.get(name, 0.0) + survey.length

    for name in sorted(stats, key=stats.get, reverse=True):
        print "%s:\t%0.1f" % (name, stats[name])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) == 1:
        print >> sys.stderr, "usage: compass_stats.py DATFILE..."
        sys.exit(2)

    compass_stats(sys.argv[1:])
