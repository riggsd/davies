#!/usr/bin/env python
"""
Prints a histogram of inclinations to show what proportion are high-angle.

usage: compass_high_angle_hist.py DATFILE...
"""

import sys

from davies import compass


def compass_stats(datfiles, bin_size=5, display_scale=3):
    histogram = [0 for bin in range(0, 91, bin_size)]

    for datfile in datfiles:
        for survey in compass.CompassDatParser(datfile).parse():
            for shot in survey:
                bin = int(abs(shot.inc) // bin_size)
                histogram[bin] += 1

    n = sum(histogram)
    high_n = sum(histogram[60/5:-1])
    high_n_percent = high_n / float(n) * 100.0

    print 'INC\tCOUNT\tPERCENT\tHISTOGRAM'
    for bin, count in enumerate(histogram):
        percent = count / float(n) * 100.0
        print '%02d\t%4d\t%5.1f%%\t%s' % (bin * bin_size, count, percent, '#' * int(round(percent * display_scale)))
    print '\t%d\t100.0%%' % n
    print 'Summary: %d (%0.1f%%) shots are high-angle 60-deg or greater' % (high_n, high_n_percent)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print >> sys.stderr, "usage: compass_high_angle_hist.py DATFILE..."
        sys.exit(2)

    compass_stats(sys.argv[1:])
