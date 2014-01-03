#!/usr/bin/env python

import sys

from davies import compass


def compass_stats(datfiles):
	stats = {}

	for datfile in datfiles:
		for survey in compass.CompassDatParser(datfile).parse():
			for shot in survey.shots:
				if shot['INC'] > 30.0:
					for name in survey.team:
						stats[name] = stats.get(name, 0) + 1

	print 'NAME\tHIGH ANGLE SHOTS'
	for name in sorted(stats, key=stats.get, reverse=True):
		print "%s:\t%d" % (name, stats[name])


if __name__ == '__main__':
	if len(sys.argv) == 1:
		print >> sys.stderr, "usage: compass_stats.py DATFILE..."
	compass_stats(sys.argv[1:])
