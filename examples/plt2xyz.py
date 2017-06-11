#!/usr/bin/env python
"""
usage: plt2xyz.py PLTFILE > outfile.xyz

Dumps an XYZ point cloud from a compiled Compass plot file, with the
assumption that all "hidden" shots are splays which represent the cave's
walls.

If the project is tied to realworld UTM coordinates, then X, Y, and Z will
be in meters. If no UTM zone is specified, then coordinates are exactly as
stored in the .PLT file (feet relative to the zero datum).
"""

from __future__ import print_function

from davies.compass.plt import CompassPltParser


FT_TO_M = 0.3048  # convert feet to meters


def plt2xyz(fname):
	"""Convert a Compass plot file to XYZ pointcloud"""
	parser = CompassPltParser(fname)
	plt = parser.parse()

	for segment in plt:
		for command in segment:
			if command.cmd == 'd':
				if plt.utm_zone:
					x, y, z = command.x * FT_TO_M, command.y * FT_TO_M, command.z * FT_TO_M
				else:
					x, y, z = command.x, command.y, command.z
				print('%.3f\t%.3f\t%.3f' % (x, y, z))


def main():
	import sys
	import logging

	logging.basicConfig()

	if len(sys.argv) < 2:
		print('usage: %s PLTFILE' % sys.argv[1], file=sys.stderr)
		sys.exit(2)

	plt2xyz(sys.argv[1])


if __name__ == '__main__':
	main()
