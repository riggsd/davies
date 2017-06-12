"""
davies.compass.plt: Module for parsing and working with Compass .PLT plot files
"""

import logging
import datetime
from collections import OrderedDict

from davies.compass import ParseException, name_from_filename

log = logging.getLogger(__name__)


__all__ = 'Plot', 'Segment', 'MoveCommand', 'DrawCommand', 'CompassPltParser'


class Command(object):
    """
    Base class for Compass .PLT plot commands.

    Note that coordinates are passed in Y, X, Z (North, East, Elevation) order!
    """
    cmd = None

    def __init__(self, y, x, z, name, l, r, u, d, edist, flags=None):
        self.y, self.x, self.z = y, x, z
        self.name = name
        self.l, self.r, self.u, self.d = l, r, u, d
        self.edist = edist
        self.flags = flags


class MoveCommand(Command):
    """Compass .PLT plot command for moving the "plotting pen" to a specified Y,X,Z coordinate."""
    cmd = 'M'


class DrawCommand(Command):
    """Compass .PLT plot command for drawing a line segment between two points."""
    cmd = 'D'


class Segment(object):
    """Compass .PLT segment. A segment is a container for :class:`Command` objects."""

    def __init__(self, name=None, date=None, comment=None):
        self.name = name
        self.date = date
        self.comment = comment
        self.xmin = self.xmax = self.ymin = self.ymax = self.zmin = self.zmax = None
        self.commands = []

    def set_bounds(self, ymin, ymax, xmin, xmax, zmin, zmax):
        """Set Y,X,Z bounds for the segment."""
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.zmin, self.zmax = zmin, zmax

    def add_command(self, command):
        """Add a :class:`Command` to :attr:`commands`."""
        self.commands.append(command)

    def __len__(self):
        return len(self.commands)

    def __iter__(self):
        for command in self.commands:
            yield command


class Plot(object):
    """Compass .PLT plot file. A Plot is a container for :class:`Segment` objects."""

    def __init__(self, name=None):
        self.name = name
        self.utm_zone = None
        self.datum = None
        self.xmin = self.xmax = self.ymin = self.ymax = self.zmin = self.zmax = self.edist = None
        self.segments = []
        self.fixed_points = OrderedDict()  # name -> (y, x, z)
        self.loop_count = 0
        self.loops = []  # list of (n, common_sta, from_sta, to_sta, [stations])

    def set_bounds(self, ymin, ymax, xmin, xmax, zmin, zmax, edist=None):
        """Set Y,X,Z bounds for the plot."""
        self.ymin, self.ymax = ymin, ymax
        self.xmin, self.xmax = xmin, xmax
        self.zmin, self.zmax = zmin, zmax
        self.edist = None

    def add_segment(self, segment):
        """Add a :class:`Segment` to :attr:`segments`."""
        self.segments.append(segment)

    def add_fixed_point(self, name, coordinate):
        """Add a (Y, X, Z) tuple to :attr:`fixed_points`."""
        self.fixed_points[name] = coordinate

    def add_loop(self, n, common_sta, from_sta, to_sta, stations):
        """Add a loop tuple to :attr:`loops`."""
        self.loops.append((n, common_sta, from_sta, to_sta, stations))

    def __len__(self):
        return len(self.segments)

    def __iter__(self):
        for segment in self.segments:
            yield segment

    def __contains__(self, item):
        for segment in self.segments:
            if item == segment.name:
                return True
        return False

    def __getitem__(self, item):
        for segment in self.segments:
            if item == segment.name:
                return segment
        raise KeyError(item)


class CompassPltParser(object):
    """Parser for Compass .PLT plot files."""
    # See:  http://www.fountainware.com/compass/Documents/FileFormats/PlotFileFormat.htm

    def __init__(self, pltfilename, strict_mode=False):
        """:param pltfilename: string filename"""
        self.pltfilename = pltfilename
        self.strict_mode = strict_mode

    def parse(self):
        """Parse our .PLT file and return :class:`Plot` object or raise :exc:`ParseException`."""
        plt = Plot(name_from_filename(self.pltfilename))

        with open(self.pltfilename, 'rb') as pltfile:
            segment = None

            for line in pltfile:
                if not line:
                    continue

                c, val = line[:1], line[1:]

                if c == 'Z':
                    edist = None
                    try:
                        ymin, ymax, xmin, xmax, zmin, zmax = (float(v) for v in val.split())
                    except ValueError:
                        ymin, ymax, xmin, xmax, zmin, zmax, _, edist = val.split()
                        ymin, ymax, xmin, xmax, zmin, zmax, edist = \
                            (float(v) for v in (ymin, ymax, xmin, xmax, zmin, zmax, edist))
                    plt.set_bounds(ymin, ymax, xmin, xmax, zmin, zmax, edist)

                elif c == 'S':
                    if not plt.name:
                        plt.name = val.strip()

                elif c == 'G':
                    plt.utm_zone = int(val)

                elif c == 'O':
                    plt.datum = val

                elif c == 'N':
                    date, comment = None, ''  # both date and comment are optional
                    try:
                        name, _, m, d, y, comment = val.split(None, 5)
                        date = datetime.date(int(y), int(m), int(d))
                    except ValueError:
                        try:
                            name, _, m, d, y = val.split()
                            date = datetime.date(int(y), int(m), int(d))
                        except ValueError:
                            name = val
                    comment = comment[1:].strip()
                    segment = Segment(name, date, comment)

                elif c == 'M':
                    flags = None  # flags are optional
                    try:
                        y, x, z, name, _, l, u, d, r, _, edist = val.split()
                    except ValueError:
                        y, x, z, name, _, l, u, d, r, _, edist, flags = val.split()
                    cmd = MoveCommand(float(y), float(x), float(z), name[1:],
                                      float(l), float(r), float(u), float(d), float(edist), flags)
                    segment.add_command(cmd)

                elif c in ('D', 'd'):
                    # 'D' for normal stations, 'd' for "hidden" stations with the 'P' flag
                    flags = None
                    try:
                        y, x, z, name, _, l, u, d, r, _, edist = val.split()
                    except ValueError:
                        y, x, z, name, _, l, u, d, r, _, edist, flags = val.split()
                    cmd = DrawCommand(float(y), float(x), float(z), name[1:],
                                      float(l), float(r), float(u), float(d), float(edist), flags)
                    cmd.cmd = c
                    segment.add_command(cmd)

                elif c == 'X':
                    segment.set_bounds(*(float(v) for v in val.split()))

                    # An X-bounds command signifies end of segment
                    plt.add_segment(segment)
                    segment = None

                elif c == 'P':
                    name, y, x, z = val.split()
                    plt.add_fixed_point(name, (float(y), float(x), float(z)))

                elif c == 'C':
                    plt.loop_count = int(val)

                elif c == 'R':
                    count, common, from_sta, to_sta, stations = val.split(None, 4)
                    plt.add_loop(int(count), common, from_sta, to_sta, stations.split())

                elif c == '\x1A':
                    continue  # "soft EOF" ascii SUB ^Z

                else:
                    msg = "Unknown PLT control code '%s': %s" % (c, val)
                    if self.strict_mode:
                        raise ParseException(msg)
                    else:
                        log.warning(msg)

        return plt
