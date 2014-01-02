#!/usr/bin/env python

import sys

from davies import compass


def compass_stats(datfiles):
	stats = {}

	for datfile in datfiles:
		for survey in compass.CompassDatParser(datfile).parse():
			for name in survey.team:
				stats[name] = stats.get(name, 0.0) + survey.length

	for name in sorted(stats, key=stats.get, reverse=True):
		print "%s:\t%0.1f" % (name, stats[name])


if __name__ == '__main__':
	if len(sys.argv) == 1:
		print >> sys.stderr, "usage: compass_stats.py DATFILE..."
	compass_stats(sys.argv[1:])
