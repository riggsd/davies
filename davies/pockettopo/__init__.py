"""
davies.pockettopo: Module for parsing and working with exported PocketTopo survey data
"""

from __future__ import division
from __future__ import print_function

import re
import codecs
import logging
from datetime import datetime
from collections import OrderedDict, defaultdict

log = logging.getLogger(__name__)

__all__ = 'TxtFile', 'Survey', 'MergingSurvey', 'Shot', 'PocketTopoTxtParser'


# TODO: properly handle zero-length shots with both from/to (station equivalence)
# TODO: older versions didn't specify units?


class Shot(OrderedDict):
    """
    Representation of a single shot in a PocketTopo Survey.

    :kwarg FROM:    (str) from station
    :kwarg TO:      (str) optional to station
    :kwarg LENGTH:  (float) distance
    :kwarg AZM:     (float) compass
    :kwarg INC:     (float) inclination
    :kwarg COMMENT: (str)
    :kwarg declination: (float) optional

    :ivar declination: (float) set or get the applied magnetic declination for the shot
    """

    def __init__(self, *args, **kwargs):
        self.declination = kwargs.pop('declination', 0.0)
        OrderedDict.__init__(self, *args, **kwargs)

        self.dupe_count = 1  # denotes averaged backsights (2) and triple-shots (3)

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
        """Corrected distance."""
        return self.get('LENGTH', -0.0)

    @property
    def is_splay(self):
        """Is this shot a "splay shot"?"""
        return self.get('TO', None) in (None, '')

    def __str__(self):
        return ', '.join('%s=%s' % (k,v) for (k,v) in self.items())

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self)


class Survey(object):
    """
    Representation of a PocketTopo Survey object. A Survey is a container for :class:`Shot` objects.
    """

    def __init__(self, name=None, date=None, comment=None, declination=0.0, cave_name=None, length_units='m', angle_units=360, shots=None):
        self.name = name
        self.date = date
        self.comment = comment
        self.declination = declination
        self.cave_name = cave_name
        self.length_units = length_units
        self.angle_units = angle_units

        self.shots = []
        self.splays = defaultdict(list)
        if shots:
            [self.add_shot(shot) for shot in shots]

    def add_shot(self, shot):
        """Add a Shot to :attr:`shots`, applying our survey's :attr:`declination` to it."""
        shot.declination = self.declination
        if shot.is_splay:
            self.splays[shot['FROM']].append(shot)
        self.shots.append(shot)

    @property
    def length(self):
        """Total surveyed cave length, not including splays."""
        return sum([shot.length for shot in self.shots if not shot.is_splay])

    @property
    def total_length(self):
        """Total surveyed length including splays."""
        return sum([shot.length for shot in self.shots])

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)

    # def _serialize(self):
    #     return []


class MergingSurvey(Survey):
    """
    Representation of a PocketTopo Survey object. A Survey is a container for :class:`Shot` objects.
    This Survey implementation merges "duplicate" shots into a single averaged shot.

    PocketTopo (and DistoX) convention is to use triple forward shots for mainline survey. When
    adding a new shot to this class with `add_shot()`, if we detect that the previous shot was
    between the same two stations, we average values and merge the two together instead of appending
    the duplicate shot. We use a "running" mean algorithm, so that this feature works for any number
    of subsequent duplicate shots (two, three, four...).
    """
    # For performance, we only look backwards at the immediately preceding shots!

    def _inverse_azm(self, azm):
        """Convert forward AZM to back AZM and vice versa"""
        return (azm + self.angle_units/2) % self.angle_units

    def _inverse_inc(self, inc):
        """Convert forward INC to back INC and vice versa"""
        return -1 * inc

    def add_shot(self, shot):
        """
        Add a shot dictionary to :attr:`shots`, applying our survey's :attr:`declination`, and
        optionally averaging and merging with duplicate previous shot.
        """
        if not self.shots or not shot.get('TO', None) or not self.shots[-1].get('TO', None):
            return super(MergingSurvey, self).add_shot(shot)

        from_, to = shot['FROM'], shot['TO']
        prev_shot = self.shots[-1]
        prev_from, prev_to = prev_shot['FROM'], prev_shot['TO']

        if from_ == prev_from and to == prev_to:
            # dupe shot! calculate iterative "running" mean and merge into the previous shot
            total_count = prev_shot.dupe_count + 1

            log.debug('Merging %d shots "%s" <- "%s"', total_count, prev_shot, shot)
            if abs(shot['AZM'] - prev_shot['AZM']) > 2.0:
                log.warning('Merged forward AZM disagreement of %0.1f for "%s" <- "%s"', abs(shot['AZM'] - prev_shot['AZM']), prev_shot, shot)
            if abs(shot['INC'] - prev_shot['INC']) > 2.0:
                log.warning('Merged forward INC disagreement of %0.1f for "%s" <- "%s"', abs(shot['INC'] - prev_shot['INC']), prev_shot, shot)
            if abs(shot['LENGTH'] - prev_shot['LENGTH']) > 1.0:
                log.warning('Merged forward LENGTH disagreement of %0.1f for "%s" <- "%s"', abs(shot['LENGTH'] - prev_shot['LENGTH']), prev_shot, shot)

            avg_length = (prev_shot['LENGTH'] * prev_shot.dupe_count + shot['LENGTH']) / total_count
            avg_azm = (prev_shot['AZM'] * prev_shot.dupe_count + shot['AZM']) / total_count
            avg_inc = (prev_shot['INC'] * prev_shot.dupe_count + shot['INC']) / total_count
            merged_comments = ('%s %s' % (prev_shot.get('COMMENT', '') or '', shot.get('COMMENT', '') or '')).strip() or None

            prev_shot['LENGTH'], prev_shot['AZM'], prev_shot['INC'], prev_shot['COMMENT'] = avg_length, avg_azm, avg_inc, merged_comments
            prev_shot.dupe_count += 1

        elif from_ == prev_to and to == prev_from:
            # backsight! we do the same iterative "running" mean rather than assuming a single forward and single back
            total_count = prev_shot.dupe_count + 1
            inv_azm, inv_inc = self._inverse_azm(shot['AZM']), self._inverse_inc(shot['INC'])

            log.debug('Merging %d backsights "%s" <- "%s"', total_count, prev_shot, shot)
            if abs(inv_azm - prev_shot['AZM']) > 2.0:
                log.warning('Backsight AZM disagreement of %0.1f for "%s" <- "%s"', abs(inv_azm - prev_shot['AZM']), prev_shot, shot)
            if abs(inv_inc - prev_shot['INC']) > 2.0:
                log.warning('Backsight INC disagreement of %0.1f for "%s" <- "%s"', abs(inv_inc - prev_shot['INC']), prev_shot, shot)
            if abs(shot['LENGTH'] - prev_shot['LENGTH']) > 1.0:
                log.warning('Backsight LENGTH disagreement of %0.1f for "%s" <- "%s"', abs(shot['LENGTH'] - prev_shot['LENGTH']), prev_shot, shot)

            avg_length = (prev_shot['LENGTH'] * prev_shot.dupe_count + shot['LENGTH']) / total_count
            avg_azm = (prev_shot['AZM'] * prev_shot.dupe_count + inv_azm) / total_count
            avg_inc = (prev_shot['INC'] * prev_shot.dupe_count + inv_inc) / total_count
            merged_comments = ('%s %s' % (prev_shot.get('COMMENT', '') or '', shot.get('COMMENT', '') or '')).strip() or None

            prev_shot['LENGTH'], prev_shot['AZM'], prev_shot['INC'], prev_shot['COMMENT'] = avg_length, avg_azm, avg_inc, merged_comments
            prev_shot.dupe_count += 1

        else:
            # a new, different shot; no merge
            return super(MergingSurvey, self).add_shot(shot)


class UTMLocation(object):
    """
    Represents a UTM-based coordinate for Reference Point.

    Note that PocketTopo doesn't support UTM Zones.

    :ivar easting:    (float)
    :ivar northing:   (float)
    :ivar elevation:  (float) meters
    :ivar comment:    (str)
    """

    def __init__(self, easting, northing, elevation=0.0, comment=None):
        self.easting = easting
        self.northing = northing
        self.elevation = elevation
        self.altitude = elevation  # alias
        self.comment = comment

    @property
    def __geo_interface__(self):
        return {'type': 'Point', 'coordinates': (self.easting, self.northing, self.elevation)}

    def __str__(self):
        return "<UTM %0.1fE %0.1fN %0.1fm>" % (self.easting, self.northing, self.elevation)


class TxtFile(object):
    """
    Representation of a PocketTopo .TXT File. A TxtFile is a container for :class:`Survey` objects.

    :ivar name:          (string) the TxtFile's "name"
    :ivar length_units:  (string) `m` (default) or `feet`
    :ivar angle_units:   (int) `360` for degrees (default) or `400` for grads
    :ivar surveys:       (list of :class:`Survey`)
    :ivar reference_points:  (dict of :class:`UTMLocation` by station)
    """

    def __init__(self, name=None, length_units='m', angle_units=360):
        self.name = name

        if length_units not in ('m', 'feet'):
            raise Exception('Length units must be either \'m\' for meters (default) or \'feet\' for feet')
        self.length_units = length_units

        if angle_units not in (360, '360', 400, '400'):
            raise Exception('Angle units must be either `360` for degrees (default) or `400` for grads')
        self.angle_units = int(angle_units)

        self.surveys = []
        self.reference_points = OrderedDict()

    def add_survey(self, survey):
        """Add a :class:`Survey` to :attr:`surveys`."""
        survey.length_units = self.length_units
        survey.angle_units = self.angle_units
        self.surveys.append(survey)

    def add_reference_point(self, station, utm_location):
        """Add a :class:`UTMLocation` to :attr:`reference_points`."""
        self.reference_points[station] = utm_location

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
    def read(fname, merge_duplicate_shots=False, encoding='windows-1252'):
        """Read a PocketTopo .TXT file and produce a `TxtFile` object which represents it"""
        return PocketTopoTxtParser(fname, merge_duplicate_shots, encoding).parse()

    # def write(self, outf):
    #     """Write a `Survey` to the specified .DAT file"""
    #     with codecs.open(outf, 'wb', 'windows-1252') as outf:
    #         for survey in self.surveys:
    #             outf.write('\r\n'.join(survey._serialize()))


class PocketTopoTxtParser(object):
    """Parses the PocketTopo .TXT file format"""

    def __init__(self, txtfilename, merge_duplicate_shots=False, encoding='windows-1252'):
        self.txtfilename = txtfilename
        self.merge_duplicate_shots = merge_duplicate_shots
        self.encoding = encoding

    def parse(self):
        """Produce a `TxtFile` object from the .TXT file"""
        log.debug('Parsing PocketTopo .TXT file %s ...', self.txtfilename)
        SurveyClass = MergingSurvey if self.merge_duplicate_shots else Survey
        txtobj = None

        with codecs.open(self.txtfilename, 'rb', self.encoding) as txtfile:
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
                survey = SurveyClass(id, date, comment, declination, cave_name)
                txtobj.add_survey(survey)

            while not lines[0]:
                lines.pop(0)  # skip blanks

            # finally actual survey data
            while lines:
                line = lines.pop(0).strip()
                if not line:
                    continue

                if '"' in line:
                    line, comment = line.split('"', 1)
                    comment = comment.rstrip('"')
                else:
                    comment = None

                if '[' not in line:
                    # this is either a Reference Point or a zero-length fake shot
                    toks = line.split()
                    if len(toks) != 4:  # ??
                        log.debug('Skipping unrecognized shot:  %s %s', line, '"%s"' % comment if comment else '')
                        continue
                    station, vals = toks[0], list(map(float, toks[1:]))
                    if vals[0] == 0.0:  # fake shot
                        log.debug('Skipping zero-length shot:  %s %s', line, '"%s"' % comment if comment else '')
                    else:  # reference point
                        easting, northing, altitude = vals
                        reference_point = UTMLocation(easting, northing, altitude, comment)
                        log.debug('Reference point:  %s', reference_point)
                        txtobj.add_reference_point(station, reference_point)
                    continue

                line, survey_id = line.split('[')
                survey_id = survey_id.rstrip().rstrip(']')
                toks = line.split()
                from_to, (length, azm, inc) = toks[:-3], (float(tok) for tok in toks[-3:])

                if len(from_to) == 2:
                    from_, to = tuple(from_to)  # shot
                elif len(from_to) == 1:
                    from_, to = from_to[0], None  # splay
                elif not from_to and length == 0.0:
                    continue  # skip junk zero-length placeholder shots
                else:
                    raise Exception()

                shot = Shot([('FROM',from_), ('TO',to), ('LENGTH',length), ('AZM',azm), ('INC',inc), ('COMMENT',comment)])
                txtobj[survey_id].add_shot(shot)

        return txtobj


if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.DEBUG)

    for fname in sys.argv[1:]:
        txtfile = PocketTopoTxtParser(fname, merge_duplicate_shots=True).parse()
        print('%s  (%s, %d)' % (txtfile.name, txtfile.length_units, txtfile.angle_units))
        for survey in txtfile:
            print('\t', '[%s] %s (%0.1f %s)' % (survey.name, survey.comment, survey.length, txtfile.length_units))
            for shot in survey:
                print('\t\t', shot)
