#!/usr/bin/env python
"""
Prints a histogram of inclinations to show what proportion are high-angle.

usage: compass_high_angle_hist.py DATFILE...


Example:

$ ./examples/compass_high_angle_hist.py mycave.dat
INC	COUNT	PERCENT	HISTOGRAM
00	2897	 31.7%	###############################################################################################
05	1635	 17.9%	######################################################
10	1051	 11.5%	##################################
15	 756	  8.3%	#########################
20	 655	  7.2%	#####################
25	 448	  4.9%	###############
30	 383	  4.2%	#############
35	 273	  3.0%	#########
40	 222	  2.4%	#######
45	 144	  1.6%	#####
50	  97	  1.1%	###
55	  51	  0.6%	##
60	  31	  0.3%	#
65	  27	  0.3%	#
70	  14	  0.2%
75	  14	  0.2%
80	   8	  0.1%
85	   6	  0.1%
90	 431	  4.7%	##############
	9143	100.0%
Summary: 100 (1.1%) shots are high-angle 60-deg or greater

"""

import sys

from davies.compass import *


def compass_stats(datfiles, bin_size=5, display_scale=3):
    histogram = [0 for bin in range(0, 91, bin_size)]

    for datfile in datfiles:
        for survey in DatFile.read(datfile):
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
