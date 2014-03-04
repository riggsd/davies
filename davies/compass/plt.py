"""
davies.compass.plt: Module for parsing and working with Compass .PLT plot files
"""

import logging
import datetime

from davies.compass import ParseException, name_from_filename

log = logging.getLogger(__name__)

__all__ = 'Plot', 'Segment', 'MoveCommand', 'DrawCommand', 'CompassPltParser'


class Command(object):
    """Base class for Compass .PLT plot commands."""
    cmd = None

    def __init__(self, x, y, z, name, l, r, u, d, ele):
        self.x, self.y, self.z = x, y, z
        self.name = name
        self.l, self.r, self.u, self.d = l, r, u, d
        self.ele = ele


class MoveCommand(Command):
    """Compass .PLT plot command for moving the "plotting pen" to a specified X,Y,Z coordinate."""
    cmd = 'M'


class DrawCommand(Command):
    """Compass .PLT plot command for drawing a line segment between two points."""
    cmd = 'D'


class Segment(object):
    """Representation of a Compass .PLT segment. A Segment is a container for :class:`Command` objects."""

    def __init__(self, name=None, date=None, comment=None):
        self.name = name
        self.date = date
        self.comment = comment
        self.xmin = self.xmax = self.ymin = self.ymax = self.zmin = self.zmax = None
        self.commands = []

    def set_bounds(self, xmin, xmax, ymin, ymax, zmin, zmax):
        """Set X,Y,Z bounds for the segment."""
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
    """Representation of a Compass .PLT plot file. A Plot is a container for :class:`Segment` objects."""

    def __init__(self, name=None):
        self.name = name
        self.utm_zone = None
        self.datum = None
        self.xmin = self.xmax = self.ymin = self.ymax = self.zmin = self.zmax = None
        self.segments = []
        self.fixed_points = {}  # name -> (x,y,z)

    def set_bounds(self, xmin, xmax, ymin, ymax, zmin, zmax):
        """Set X,Y,Z bounds for the plot."""
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.zmin, self.zmax = zmin, zmax

    def add_segment(self, segment):
        """Add a :class:`Segment` to :attr:`segments`."""
        self.segments.append(segment)

    def add_fixed_point(self, name, coordinate):
        """Add an (X, Y, Z) tuple to :attr:`fixed_points`."""
        self.fixed_points[name] = coordinate

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

    def __init__(self, pltfilename):
        """:param pltfilename: string filename"""
        self.pltfilename = pltfilename

    def parse(self):
        """Parse our .PLT file and return :class:`Plot` object or raise :exc:`ParseException`."""
        plt = Plot(name_from_filename(self.pltfilename))

        with open(self.pltfilename, 'rb') as pltfile:
            first_line = pltfile.readline()
            c, val = first_line[:1], first_line[1:]

            segment = None

            for line in pltfile:
                if not line:
                    continue

                c, val = line[:1], line[1:]

                if c == 'Z':
                    plt.set_bounds(*(float(v) for v in val.split()))

                if c == 'S':
                    # this is probably more appropriately called a "segment"
                    if not plt.name:
                        plt.name = val.strip()

                elif c == 'G':
                    plt.utm_zone = int(val)

                elif c == 'O':
                    plt.datum = val

                elif c == 'N':
                    name, _, m, d, y, comment = val.split(None, 5)
                    comment = comment[1:].strip()
                    date = datetime.date(int(y), int(m), int(d))
                    segment = Segment(name, date, comment)

                elif c == 'M':
                    x, y, z, name, _, l, u, d, r, _, ele = val.split()
                    cmd = MoveCommand(float(x), float(y), float(z), name[1:], float(l), float(r), float(u), float(d), float(ele))
                    segment.add_command(cmd)

                elif c == 'D':
                    x, y, z, name, _, l, u, d, r, _, ele = val.split()
                    cmd = DrawCommand(float(x), float(y), float(z), name[1:], float(l), float(r), float(u), float(d), float(ele))
                    segment.add_command(cmd)

                elif c == 'X':
                    segment.set_bounds(*(float(v) for v in val.split()))

                    # An X-bounds command signifies end of segment
                    plt.add_segment(segment)
                    segment = None

                elif c == 'P':
                    name, x, y, z = val.split()
                    plt.add_fixed_point(name, (float(x), float(y), float(z)))

                elif c == '\x1A':
                    continue  # "soft EOF" ascii SUB ^Z

                else:
                    raise ParseException("Unknown PLT control code '%s': %s" % (c, val))

        return plt
