#!/usr/bin/env python2
"""
This simple example file illustrates a conversion from PocketTopo .TXT export
to a Therion .TH centerline file. Note that this requires the .TXT export from
PocketTopo, *not* the kludge "Therion Export" text file which requires a
subsequent import from within Therion's graphical editor.

usage: pockettopo2therion.py TXTFILE...

"""

import sys
import os, os.path
import logging

from davies import pockettopo


def convert_filename(txtfilename, outdir='.'):
    """Convert a .TXT filename to a Therion .TH filename"""
    return os.path.join(outdir, os.path.basename(txtfilename)).rsplit('.', 1)[0] + '.th'


def pockettopo2therion(txtfilename):
    """Main function which converts a PocketTopo .TXT file to a Compass .DAT file"""
    print 'Converting PocketTopo data file %s ...' % txtfilename
    infile = pockettopo.TxtFile.read(txtfilename, merge_duplicate_shots=True)
    outfilename = convert_filename(txtfilename)

    with open(outfilename, 'w') as outfile:
        print >> outfile, 'encoding utf-8'
        for insurvey in infile:
            print >> outfile
            print >> outfile, 'centreline'
            print >> outfile, '\t' 'date ' + insurvey.date.strftime('%Y.%m.%d')
            print >> outfile, '\t' 'data normal from to compass clino tape'
            for shot in insurvey:
                print >> outfile, '\t' '%s\t%s\t%7.2f\t%7.2f\t%6.2f' % \
                                  (shot['FROM'], shot.get('TO', None) or '-',
                                   shot.azm, shot.inc, shot.length)
            print >> outfile, 'endcentreline'
        print 'Wrote Therion data file %s .' % outfilename


def thconfig(txtfiles, cavename='cave'):
    """Write `thconfig` file for the Therion project"""
    fmts_model = ['lox', '3d', 'dxf', 'kml', 'plt', 'vrml']
    outfilename = 'thconfig'

    with open(outfilename, 'w') as outfile:
        for txtfilename in txtfiles:
            print >> outfile, 'source "%s"' % convert_filename(txtfilename)
        print >> outfile

        for fmt in fmts_model:
            print >> outfile, 'export model -output "%s"' % os.path.join('models', '%s.%s' % (cavename, fmt))

        print >> outfile, 'export map -projection plan -format esri -output "%s"' % os.path.join('models', 'gis')

        print 'Wrote Therion project file %s .' % outfilename


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        print >> sys.stderr, 'usage: %s TXTFILE...' % os.path.basename(sys.argv[0])
        sys.exit(2)

    txtfiles = sys.argv[1:]
    for txtfilename in txtfiles:
        pockettopo2therion(txtfilename)
    thconfig(txtfiles)
