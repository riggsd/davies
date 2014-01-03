#!/usr/bin/env python

import sys

import networkx as nx

from matplotlib import pyplot

from davies import compass


def pltparser(pltfilename):
	parser = compass.CompassPltParser(pltfilename)
	plt = parser.parse()


	g = nx.Graph()
	pos = {}
	ele = {}
	for segment in plt:
		prev = None

		for cmd in segment:
			pos[cmd.name] = (-cmd.x, cmd.y)
			ele[cmd.name] = cmd.z
			if not prev or cmd.cmd == 'M':
				prev = cmd  # move
				continue
			g.add_edge(prev.name, cmd.name)
			prev = cmd

	pyplot.figure().suptitle(plt.name, fontweight='bold')
	colors = [ele[n] for n in g]
	nx.draw(g, pos, node_color=colors, vmin=min(colors), vmax=max(colors), with_labels=False, node_size=15)
	pyplot.show()


if __name__ == '__main__':
	pltparser(sys.argv[1])
