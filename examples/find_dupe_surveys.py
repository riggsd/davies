#!/usr/bin/env python
"""
Find duplicated survey designations
"""

import sys
from os.path import basename

from davies.compass import *


def find_dupe_surveys(fnames):
    surveyd = {}  # cave name -> set of survey names
    for fname in fnames:
        dat = DatFile.read(fname)
        surveyd[basename(fname)] = set(survey.name for survey in dat)
    surveyd2 = dict(surveyd)  # mutable copy to avoid dupe comparisons
    for cave1, surveys1 in surveyd.items():
        surveyd2.pop(cave1)
        for cave2, surveys2 in surveyd2.items():
            conflicts = surveys1 & surveys2
            if conflicts:
                print '%s - %s:\t%s' % (cave1, cave2, ', '.join(conflicts))
                

if __name__ == '__main__':
    find_dupe_surveys(sys.argv[1:])
