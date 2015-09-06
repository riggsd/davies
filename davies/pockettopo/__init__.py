"""
davies.pockettopo: Module for parsing and working with exported PocketTopo survey data
"""

import re
import sys
import codecs
import logging
from datetime import datetime
from collections import OrderedDict

log = logging.getLogger(__name__)


# TODO: optionally combine triple-shots and backsights
# TODO: properly handle zero-length shots with from/to, which define station equivalence
# TODO: handle fixed stations / reference points
# TODO: older versions didn't specify units


class Shot(OrderedDict):
    """
    Representation of a single shot in a PocketTopo Survey.

    :kwarg FROM:
    :kwarg TO:
    :kwarg LENGTH:
    :kwarg AZM:
    :kwarg INC:
    :kwarg declination:

    :ivar declination:
    """

    def __init__(self, *args, **kwargs):
        self.declination = kwargs.pop('declination', 0.0)
        OrderedDict.__init__(self, *args, **kwargs)

    @property
    def azm(self):
        """Corrected azimuth, taking into account declination."""
        return self.get('AZM', -0.0) + self.declination

    @property
    def inc(self):
        """Corrected inclination."""
        return self.get('INC', -0.0)

    @property
    def length(self):
        """Corrected distance, taking into account tape correction."""
        return self.get('LENGTH', -0.0)

    @property
    def is_splay(self):
        """Is this shot a "splay shot"?"""
        return self.get('TO', None) in (None, '')


class Survey(object):
    """Representation of a PocketTopo Survey object. A Survey is a container for :class:`Shot` objects."""

    def __init__(self, name=None, date=None, comment=None, declination=0.0, cave_name=None, shots=None):
        self.name = name
        self.date = date
        self.comment = comment
        self.declination = declination
        self.cave_name = cave_name
        self.shots = shots if shots else []

    def add_shot(self, shot):
        """Add a shot dictionary to :attr:`shots`."""
        self.shots.append(shot)

    @property
    def length(self):
        """Total surveyed length, not including splays."""
        return sum([shot.length for shot in self.shots if not shot.is_splay])

    def __len__(self):
        return len(self.shots)

    def __iter__(self):
        for shot in self.shots:
            yield shot

    def __contains__(self, item):
        for shot in self.shots:
            if item in (shot.get('FROM', None), shot.get('TO', None)):
                return True
        return False

    # def _serialize(self):
    #     return []


class TxtFile(object):
    """
    Representation of a PocketTopo .TXT File. A TxtFile is a container for :class:`Survey` objects.

    :ivar name:    (string) the TxtFile's "name"
    :ivar length_units: (string) `meters` (default) or `feet`
    :ivar angle_units: (int) `360` for degrees (default) or `400` for grads
    :ivar surveys: (list of :class:`Survey`)
    """

    def __init__(self, name=None, length_units='meters', angle_units=360):
        self.name = name
        self.length_units = length_units
        self.angle_units = angle_units

        self.surveys = []

    def add_survey(self, survey):
        """Add a :class:`Survey` to :attr:`surveys`."""
        self.surveys.append(survey)

    @property
    def length(self):
        """Total surveyed length."""
        return sum([survey.length for survey in self.surveys])

    def __len__(self):
        return len(self.surveys)

    def __iter__(self):
        for survey in self.surveys:
            yield survey

    def __contains__(self, item):
        for survey in self.surveys:
            if item == survey.name or item == survey:
                return True
        return False

    def __getitem__(self, item):
        for survey in self.surveys:
            if item == survey.name or item == survey:
                return survey
        raise KeyError(item)

    @staticmethod
    def read(fname):
        """Read a .DAT file and produce a `Survey`"""
        return PocketTopoTxtParser(fname).parse()

    # def write(self, outf):
    #     """Write a `Survey` to the specified .DAT file"""
    #     with codecs.open(outf, 'wb', 'windows-1252') as outf:
    #         for survey in self.surveys:
    #             outf.write('\r\n'.join(survey._serialize()))
    #             outf.write('\r\n'+'\f'+'\r\n')  # ASCII "form feed" ^L
    #         outf.write('\x1A')  # ASCII "sub" ^Z marks EOF


class PocketTopoTxtParser(object):

    def __init__(self, txtfilename):
        self.txtfilename = txtfilename

    def parse(self):
        log.debug('Parsing PocketTopo .TXT file %s ...', self.txtfilename)
        txtobj = None

        with codecs.open(self.txtfilename, 'rb', 'windows-1252') as txtfile:
            lines = txtfile.read().splitlines()

            # first line is cave name and units
            first_line_re = re.compile(r'^([\w\s]*)\(([\w\s]*),([\w\s]*)')
            first_line = lines.pop(0)
            cave_name, length_units, angle_units = first_line_re.search(first_line).groups()
            cave_name, angle_units = cave_name.strip(), int(angle_units)
            txtobj = TxtFile(cave_name, length_units, angle_units)

            while not lines[0]:
                lines.pop(0)  # skip blanks

            # next block identifies surveys (trip) metadata
            while lines[0].startswith('['):
                toks = lines.pop(0).split(None, 3)
                id, date, declination = toks[:3]
                id = id.strip('[]:')
                date = datetime.strptime(date, '%Y/%m/%d').date()
                declination = float(declination)
                comment = toks[3].strip('"') if len(toks) == 4 else ''
                survey = Survey(id, date, comment, declination, cave_name)
                txtobj.add_survey(survey)

            while not lines[0]:
                lines.pop(0)  # skip blanks

            # finally actual survey data
            while lines:
                line = lines.pop().strip()
                if not line:
                    continue

                if '"' in line:
                    line, comment = line.split('"', 1)
                    comment = comment.rstrip('"')
                else:
                    comment = None

                if '[' not in line:
                    continue  # junk zero-length shots, skip?

                line, survey_id = line.split('[')
                survey_id = survey_id.rstrip().rstrip(']')
                toks = line.split()
                from_to, (length, azm, inc) = toks[:-3], (float(tok) for tok in toks[-3:])

                if len(from_to) == 2:
                    # shot
                    from_, to = tuple(from_to)
                elif len(from_to) == 1:
                    # splay
                    from_, to = from_to[0], None
                elif not from_to and length == 0.0:
                    continue  # skip junk zero-length placeholder shots
                else:
                    raise Exception()

                shot = Shot(FROM=from_, TO=to, LENGTH=length, AZM=azm, INC=inc, COMMENT=comment, declination=declination)
                txtobj[survey_id].add_shot(shot)

        return txtobj


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    for fname in sys.argv[1:]:
        txtfile = PocketTopoTxtParser(fname).parse()
        print '%s  (%s, %d)' % (txtfile.name, txtfile.length_units, txtfile.angle_units)
        for survey in txtfile:
            print '\t', '[%s] %s (%0.1f %s)' % (survey.name, survey.comment, survey.length, txtfile.length_units)
            for shot in survey:
                print '\t\t', shot
