#!/usr/bin/env python2
"""
This simple example file illustrates a conversion from PocketTopo .TXT survey to a Compass .DAT
survey. The general idea is simple, but "the devil is in the details"; Davies doesn't gloss over
the differences in each format, so we must carefully convert from one shot format to the other, as
well has "hack" a few nuances.

usage: pockettopo2compass.py TXTFILE...

"""

import sys
import os, os.path
import logging
import random

from davies import compass
from davies import pockettopo


def shot2shot(inshot):
    """Convert a PocketTopo `Shot` to a Compass `Shot`"""
    return compass.Shot([
        ('FROM', inshot['FROM']),
        # Compass requires a named TO station, so we must invent one for splays
        ('TO', inshot['TO'] or '%s.s%03d' % (inshot['FROM'], random.randint(0,1000))),
        ('LENGTH', inshot.length),
        # BEARING/AZM named inconsistently in Davies to reflect each program's arbitrary name. We
        # can't use `inshot.azm` here because we need the "raw" compass value without declination
        ('BEARING', inshot['AZM']),
        ('INC', inshot.inc),
        # LRUD required in Compass, but faked here
        ('LEFT', 0.0), ('RIGHT', 0.0), ('UP', 0.0), ('DOWN', 0.0),
        # Compass 'L' flag excludes splays from cave length calculation
        ('FLAGS', (compass.Exclude.LENGTH,) if inshot.is_splay else ()),
        # COMMENTS/COMMENT named inconsistently in Davies to reflect each program's arbitrary name
        ('COMMENTS', inshot['COMMENT'])
    ])


def pockettopo2compass(txtfilename, exclude_splays=False):
    """Main function which converts a PocketTopo .TXT file to a Compass .DAT file"""
    print 'Converting PocketTopo data file %s ...' % txtfilename

    # Read our PocketTopo .TXT file, averaging triple-shots in the process
    infile = pockettopo.TxtFile.read(txtfilename, merge_duplicate_shots=True)

    cave_name = os.path.basename(txtfilename).rsplit('.', 1)[0].replace('_', ' ')
    outfilename = txtfilename.rsplit('.', 1)[0] + '.DAT'

    # Create the Compass DatFile in memory and start building, we'll write to file when done
    outfile = compass.DatFile(cave_name)

    for insurvey in infile:
        # Our Compass and PocketTopo Surveys are very similar...
        outsurvey = compass.Survey(
            insurvey.name, insurvey.date, comment=insurvey.comment, cave_name=cave_name, declination=insurvey.declination
        )
        for inshot in insurvey:
            if inshot.is_splay and exclude_splays:
                continue  # skip

            # ...but the Shot data fields require some tweaking, see `shot2shot()` for details
            outshot = shot2shot(inshot)
            outsurvey.add_shot(outshot)

        # We have to hack a few Compass details dealing with units and field ordering for now
        outsurvey.shot_header = outshot.keys()  # FIXME?
        outsurvey.lrud_format = 'DDDDLRUDLADN'  # FIXME?
        outfile.add_survey(outsurvey)

    # Finally all built, dump the whole DatFile/Surveys/Shots structure to file
    outfile.write(outfilename)
    print 'Wrote Compass data file %s .' % outfilename


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        print >> sys.stderr, 'usage: %s TXTFILE...' % os.path.basename(sys.argv[0])
        sys.exit(2)

    for txtfilename in sys.argv[1:]:
        pockettopo2compass(txtfilename)
