#!/usr/bin/env python
"""
Print cumulative survey footage over a project's history
"""
import sys
import os.path
from collections import Counter

from davies.compass import *


def print_cumulative_footage(datfiles):
    total = 0.0                # miles
    monthly_stats = Counter()  # feet per month
    cumulative_stats = {}      # cumulative miles by month

    for datfilename in datfiles:
        print datfilename, '...'
        datfile = DatFile.read(datfilename)
        for survey in datfile:
            month = survey.date.strftime('%Y-%m')
            monthly_stats[month] += survey.included_length

    print 'MONTH\tFEET\tTOTAL MILES'
    for month in sorted(monthly_stats.keys()):
        total += monthly_stats[month] / 5280.0
        cumulative_stats[month] = total
        print '%s\t%5d\t%5.1f' % (month, monthly_stats[month], total)
    

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, 'usage: %s DATFILE...' % os.path.basename(sys.argv[0])
        sys.exit(2)
    datfiles = sys.argv[1:]
    print_cumulative_footage(datfiles)
