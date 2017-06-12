"""
davies.compass: Module for parsing and working with Compass source files
"""

import os.path
import logging
import datetime
import codecs
from collections import OrderedDict

log = logging.getLogger(__name__)

__all__ = 'Project', 'UTMLocation', 'UTMDatum', \
          'DatFile', 'Survey', 'Shot', 'Exclude', \
          'CompassProjectParser', 'CompassDatParser', 'ParseException'


# Compass OO Model


DEFAULT_HEADER = ['FROM', 'TO', 'LENGTH', 'BEARING', 'INC', 'LEFT', 'UP', 'DOWN', 'RIGHT', 'FLAGS', 'COMMENTS']
DEFAULT_HEADER_BACKSIGHTS = ['FROM', 'TO', 'LENGTH', 'BEARING', 'INC', 'LEFT', 'UP', 'DOWN', 'RIGHT', 'AZM2', 'INC2', 'FLAGS', 'COMMENTS']


class Exclude:
    """Shot flags"""
    LENGTH  = 'L'
    TOTAL   = 'X'
    CLOSURE = 'C'
    PLOT    = 'P'


class Shot(OrderedDict):
    """
    Representation of a single shot in a Compass Survey.

    See: `Compass Survey Data File Format <http://www.fountainware.com/compass/Documents/FileFormats/SurveyDataFormat.htm>`_
    """
    # FIXME: support compass, back-compass, and tape corrections

    def __init__(self, *args, **kwargs):
        """
        :kwarg FROM:    (str) from station
        :kwarg TO:      (str) to station
        :kwarg BEARING: (float) forward compass in **decimal degrees**
        :kwarg AZM2:    (float) back compass in **decimal degrees**
        :kwarg INC:     (float) forward inclination in **decimal degrees**
        :kwarg INC2:    (float) back inclination in **decimal degrees**
        :kwarg LENGTH:  (float) distance in **decimal feet**
        :kwarg FLAGS:   (collection of :class:`Exclude`) shot exclusion flags
        :kwarg COMMENTS: (str) text comments, up to 80 characters long
        :kwarg declination: (float) magnetic declination in decimal degrees

        :ivar declination: (float) set or get magnetic declination adjustment
        """
        self.declination = kwargs.pop('declination', 0.0)
        OrderedDict.__init__(self, *args, **kwargs)

    @property
    def azm(self):
        """Corrected azimuth, taking into account backsight, declination, and compass corrections."""
        azm1 = self.get('BEARING', None)
        azm2 = self.get('AZM2', None)
        if azm1 is None and azm2 is None:
            return None
        if azm2 is None:
            return azm1 + self.declination
        if azm1 is None:
            return (azm2 + 180) % 360 + self.declination
        return (azm1 + (azm2 + 180) % 360) / 2.0 + self.declination

    @property
    def inc(self):
        """Corrected inclination, taking into account backsight and clino corrections."""
        inc1 = self.get('INC', None)
        inc2 = self.get('INC2', None)
        if inc1 is None and inc2 is None:
            return None
        if inc2 is None:
            return inc1
        if inc1 is None:
            return -1 * inc2
        return (inc1 - inc2) / 2.0

    @property
    def flags(self):
        """Shot exclusion flags as a `set`"""
        return set(self.get('FLAGS', ''))  # older data may not have FLAGS field

    @property
    def length(self):
        """Corrected distance, taking into account tape correction."""
        return self.get('LENGTH', None)

    @property
    def is_included(self):
        return Exclude.LENGTH not in self.flags and Exclude.TOTAL not in self.flags

    @property
    def is_excluded(self):
        return Exclude.LENGTH in self.flags or Exclude.TOTAL in self.flags

    def __str__(self):
        return ', '.join('%s=%s' % (k,v) for (k,v) in self.items())

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self)


class Survey(object):
    """
    Representation of a Compass Survey object. A Survey is a container for :class:`Shot` objects.

    See: `Compass Survey Data File Format <http://www.fountainware.com/compass/Documents/FileFormats/SurveyDataFormat.htm>`_

    :ivar file_format: (str) format string which defines how Compass will view/edit underlying \
                             survey data; setting this property will in turn set all the other file \
                             format properties listed below; should be a string of 11 - 13 characters
    :ivar bearing_units: (chr) 'D'
    :ivar length_units: (chr) 
    :ivar passage_units: (chr) 
    :ivar inclination_units: (chr) 
    :ivar passage_dimension_order: (list of chr)
    :ivar shot_item_order: (list of chr) 
    :ivar backsight: (chr) 
    :ivar lrud_association: (chr) 
    """

    def __init__(self, name='', date=None, comment='', team='', declination=0.0, file_format=None, corrections=(0.0,0.0,0.0), corrections2=(0.0,0.0), cave_name='', shot_header=(), shots=None):
        self.name = name
        self.date = date
        self.comment = comment
        self.team = team
        self.declination = declination
        self.corrections, self.corrections2 = corrections, corrections2  # TODO: instrument corrections not supported
        self.cave_name = cave_name
        self.shot_header = shot_header  # FIXME: this ordering is not optional!
        self.shots = shots if shots else []

        self.bearing_units = 'D'
        self.length_units = 'D'
        self.passage_units = 'D'
        self.inclination_units = 'D'
        self.passage_dimension_order = ['U','D','L','R']
        self.shot_item_order = ['L', 'A', 'D']
        self.backsight = 'N'
        self.lrud_association = 'F'
        if file_format:
            self.file_format = file_format

    @property
    def file_format(self):
        return '%s%s%s%s%s%s%s%s' % \
               (self.bearing_units, self.length_units, self.passage_units, self.inclination_units,
                ''.join(self.passage_dimension_order), ''.join(self.shot_item_order),
                self.backsight, self.lrud_association)

    @file_format.setter
    def file_format(self, fmt):
        if len(fmt) < 11:
            raise ValueError(fmt)
        self.bearing_units = fmt[0]
        self.length_units = fmt[1]
        self.passage_units = fmt[2]
        self.inclination_units = fmt[3]
        self.passage_dimension_order = list(fmt[4:8])

        if len(fmt) < 15:
            self.shot_item_order = list(fmt[8:11])
        else:
            self.shot_item_order = list(fmt[8:13])

        if len(fmt) < 12:
            self.backsight = 'N'
        elif len(fmt) > 12:
            self.backsight = fmt[-2]
        else:
            self.backsight = fmt[-1]

        if len(fmt) < 13:
            self.lrud_association = 'F'
        else:
            self.lrud_association = fmt[-1]

    def add_shot(self, shot):
        """Add a shot dictionary to :attr:`shots`, applying this survey's magnetic declination"""
        shot.declination = self.declination
        self.shots.append(shot)

    @property
    def length(self):
        """Total surveyed length, regardless of exclusion flags."""
        return sum([shot.length for shot in self.shots])

    @property
    def included_length(self):
        """Surveyed length, not including "excluded" shots"""
        return sum([shot.length for shot in self.shots if shot.is_included])

    @property
    def excluded_length(self):
        """Surveyed length which does not count toward the included total"""
        return sum([shot.length for shot in self.shots if Exclude.LENGTH in shot.flags or Exclude.TOTAL in shot.flags])

    @property
    def backsights_enabled(self):
        for shot in self:
            if 'AZM2' in shot or 'INC2' in shot:
                return True
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

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

    def _serialize(self):
        date = self.date.strftime('%m %d %Y').lstrip('0') if self.date else ''
        if self.shot_header:
            header = self.shot_header
        else:
            header = DEFAULT_HEADER_BACKSIGHTS if self.backsights_enabled else DEFAULT_HEADER
        
        lines = [
            self.cave_name,
            'SURVEY NAME: %s' % self.name,
            'SURVEY DATE: %s  COMMENT:%s' % (date, self.comment),
            'SURVEY TEAM:',
            ','.join(self.team) if self.team else '',
            'DECLINATION: %7.2f  FORMAT: %s  CORRECTIONS:  %s  CORRECTIONS2:  %s' %
                (self.declination, self.file_format,
                 '%.2f %.2f %.2f' % tuple(self.corrections),
                 '%.2f %.2f' % tuple(self.corrections2)),
            '',
            '\t'.join(header),
            '',
        ]
        for shot in self.shots:
            vals = []
            for k in header:
                v = shot.get(k, None)
                if k in ('BEARING', 'INC', 'AZM2', 'INC2'):
                    vals.append('%7.2f' % (v if v is not None else -999.0))
                elif k == 'LENGTH':
                    vals.append('%8.3f' % (v if v is not None else -999.0))
                elif k in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
                    vals.append('%7.2f' % (v if v is not None and v != float('inf') else -9.90))
                elif k in ('FROM', 'TO'):
                    v = v or ''
                    vals.append(v.rjust(6))
                elif k in ('FLAGS', 'COMMENTS'):
                    pass  # handle them together below
                else:
                    vals.append(str(v) if v is not None else '')

            if shot.get('FLAGS', ''):
                flags = '#|%s#' % ''.join(list(shot.get('FLAGS', ())))
                vals.append('%s  %s' % (flags, shot.get('COMMENTS', '') or ''))
            else:
                vals.append((shot.get('COMMENTS', '') or '')[:80])

            lines.append('\t'.join(vals))
        return lines


class DatFile(object):
    """
    Representation of a Compass .DAT File. A DatFile is a container for :class:`Survey` objects.

    See: `Compass Survey Data File Format <http://www.fountainware.com/compass/Documents/FileFormats/SurveyDataFormat.htm>`_

    :ivar name:     (string) the DatFile's "name", not necessarily related to its filename
    :ivar filename: (string) underlying .DAT file's filename
    :ivar surveys:  (list of :class:`Survey`)
    """

    def __init__(self, name=None, filename=None):
        self.name = name
        self.filename = filename
        self.surveys = []

    def add_survey(self, survey):
        """Add a :class:`Survey` to :attr:`surveys`."""
        self.surveys.append(survey)

    @property
    def length(self):
        """Total surveyed length."""
        return sum([survey.length for survey in self.surveys])

    @property
    def included_length(self):
        """Surveyed length, not including "excluded" shots"""
        return sum([survey.included_length for survey in self.surveys])

    @property
    def excluded_length(self):
        """Surveyed length which does not count toward the included total"""
        return sum([survey.excluded_length for survey in self.surveys])

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
        return CompassDatParser(fname).parse()

    def write(self, outfname=None):
        """Write or overwrite a `Survey` to the specified .DAT file"""
        outfname = outfname or self.filename
        with codecs.open(outfname, 'wb', 'windows-1252') as outf:
            for survey in self.surveys:
                outf.write('\r\n'.join(survey._serialize()))
                outf.write('\r\n'+'\f'+'\r\n')  # ASCII "form feed" ^L
            outf.write('\x1A')  # ASCII "sub" ^Z marks EOF


class UTMDatum:
    """Enumeration of common geographic datums."""
    NAD27 = 'North American 1927'
    NAD83 = 'North American 1983'
    WGS84 = 'WGS 1984'


class UTMLocation(object):
    """Represents a UTM-based coordinate for fixed stations."""

    def __init__(self, easting, northing, elevation=0.0, zone=0, datum=None, convergence=0.0):
        self.easting = float(easting)
        self.northing = float(northing)
        self.elevation = float(elevation)
        self.zone = int(zone)
        self.convergence = float(convergence)
        self.datum = datum

    @property
    def __geo_interface__(self):
        return {'type': 'Point', 'coordinates': (self.easting, self.northing, self.elevation)}

    def __str__(self):
        return "<%s UTM Zone %s %0.1fE %0.1fN %0.1f>" % (self.datum, self.zone, self.easting, self.northing, self.elevation)


class Project(object):
    """
    Representation of a Compass .MAK Project file. A Project is a container for :class:`DatFile` objects.

    See: `Compass Project File Format <http://www.fountainware.com/compass/Documents/FileFormats/ProjectFileFormat.htm>`_
    
    :ivar name:          (string)
    :ivar filename:      (string)
    :ivar base_location: (:class:`UTMLocation`)
    :ivar linked_files:  (list of :class:`DatFile`)
    :ivar fixed_stations: (map of :class:`DatFile` -> station -> :class:`UTMLocation`)
    """
    
    def __init__(self, name=None, filename=None):
        self.name = name
        self.filename = filename
        
        self.linked_files = []
        self.fixed_stations = {}  # datfile -> station -> UTMLocation

        self.base_location = None
        self._utm_zone = None
        self._utm_datum = None
        self._utm_convergence = None

        # TODO: file parameters
        self.override_lrud = False
        self.lrud_association = 'FROM'  # or 'TO'

    def set_base_location(self, location):
        """Configure the project's base location"""
        self.base_location = location
        self._utm_zone = location.zone
        self._utm_datum = location.datum
        self._utm_convergence = location.convergence

    def add_linked_file(self, datfile):
        """Add a :class:`DatFile` to :attr:`linked_files`."""
        self.linked_files.append(datfile)

    def add_linked_station(self, datfile, station, location=None):
        """Add a linked or fixed station"""
        if datfile not in self.fixed_stations:
            self.fixed_stations[datfile] = {station: location}
        else:
            self.fixed_stations[datfile][station] = location

        if location and not self.base_location:
            self._utm_zone = location.zone
            self._utm_datum = location.datum
            self._utm_convergence = location.convergence

    def __len__(self):
        return len(self.linked_files)

    def __iter__(self):
        for linked_file in self.linked_files:
            yield linked_file

    def __getitem__(self, item):
        for datfile in self.linked_files:
            if item == datfile.name or item == datfile:
                return datfile
        raise KeyError(item)

    @staticmethod
    def read(fname):
        """Read a .MAK file and produce a `Project`"""
        return CompassProjectParser(fname).parse()

    def _serialize(self):
        lines = []
        if self.base_location:
            loc = self.base_location
            lines.append('@%.3f,%.3f,%.3f,%d,%.3f;' % (loc.easting, loc.northing, loc.elevation, loc.zone, loc.convergence))
            lines.append('&%s;' % loc.datum)
        
        override = 'O' if self.override_lrud else 'o'
        association = 't' if self.lrud_association == 'FROM' else 'T'
        lines.append('!%s%s;' % (override, association))

        if self._utm_zone:
            lines.append('$%d;' % self._utm_zone)
        if self._utm_datum:
            lines.append('&%s;' % self._utm_datum)
        if self._utm_convergence:
            lines.append('%%%.2f;' % self._utm_convergence)

        for dat in self.linked_files:
            datfname = dat.filename if type(dat) == DatFile else dat
            if not datfname.lower().endswith('.dat'):
                raise ValueError('Unable to locate MAK file "%s"' % dat)
            if dat not in self.fixed_stations:
                lines.append('#%s;' % datfname)
            else:
                lines.append('#%s,' % datfname)
                for station, loc in self.fixed_stations[dat].items():
                    if loc:
                        lines.append('\t%s[m,%.3f,%.3f,%.3f,],' % (station, loc.easting, loc.northing, loc.elevation))
                    else:
                        lines.append('\t%s,' % station)
                lines.append(';')
        
        return lines

    def write(self, outfilename=None):
        """Write or overwrite this .MAK file"""
        outfilename = outfilename or self.filename
        if not outfilename:
            raise ValueError('Unable to write MAK file without a filename')
        with codecs.open(outfilename, 'wb', 'windows-1252') as outf:
            outf.write('\r\n'.join(self._serialize()))
            #outf.write('\x1A')  # ASCII "sub" ^Z marks EOF



# File Parsing Utilities


_FLOAT_KEYS = ['LENGTH', 'BEARING', 'AZM2', 'INC', 'INC2', 'LEFT', 'RIGHT', 'UP', 'DOWN']
_INF_KEYS = ['LEFT', 'RIGHT', 'UP', 'DOWN']


def name_from_filename(fname):
    return os.path.splitext(os.path.basename(fname))[0].replace('_', ' ')


class ParseException(Exception):
    """Exception raised when parsing fails."""
    pass


class CompassSurveyParser(object):
    """Parser for a Compass survey string."""

    def __init__(self, survey_str):
        """:param survey_str: string multiline representation of survey as found in .DAT file"""
        self.survey_str = survey_str

    @staticmethod
    def _coerce(key, val):
        if val == '-999.00':  # no data
            return None

        if key in _INF_KEYS and val in ('-9.90', '-9999.00'):  # passage
            return float('inf')

        if key in _FLOAT_KEYS:
            try:
                return float(val)
            except TypeError as e:
                log.warn("Unable to coerce to float %s=%s (%s)", key, val, type(val))

        return val

    @staticmethod
    def _parse_date(datestr):
        datestr = datestr.strip()
        for fmt in ['%m %d %Y', '%m %d %y']:
            try:
                return datetime.datetime.strptime(datestr, fmt).date()
            except ValueError:
                pass
        raise ParseException("Unable to parse SURVEY DATE: %s" % datestr)

    @staticmethod
    def _parse_declination_line(line):
        declination, fmt, corrections, corrections2 = 0.0, '', (0.0, 0.0, 0.0), (0.0, 0.0)
        toks = line.strip().split()
        for i, tok in enumerate(toks):
            if tok == 'DECLINATION:':
                declination = float(toks[i+1])
            elif tok == 'FORMAT:':
                fmt = toks[i+1]
            elif tok == 'CORRECTIONS:':
                corrections = map(float, toks[i+1:i+4])
            elif tok == 'CORRECTIONS2:':
                corrections2 = map(float, toks[i+1:i+3])
        return declination, fmt, corrections, corrections2

    def parse(self):
        """Parse our string and return a Survey object, None, or raise :exc:`ParseException`"""
        if not self.survey_str:
            return None
        lines = self.survey_str.splitlines()
        if len(lines) < 10:
            raise ParseException("Expected at least 10 lines in a Compass Survey, only found %d!\nlines=%s" % (len(lines), lines))

        # undelimited Cave Name may be empty string and "skipped"
        first_line = lines.pop(0).strip()
        if first_line.startswith('SURVEY NAME:'):
            cave_name = ''
            name = first_line.strip('SURVEY NAME:').strip()
        else:
            cave_name = first_line
            name = lines.pop(0).split('SURVEY NAME:', 1)[1].strip()

        # Date and Comment on one line, Comment may be missing
        date_comment_toks = lines.pop(0).split('SURVEY DATE:', 1)[1].split('COMMENT:')
        date = CompassSurveyParser._parse_date(date_comment_toks[0])
        comment = date_comment_toks[1].strip() if len(date_comment_toks) > 1 else ''

        lines.pop(0)  # SURVEY TEAM:\n (actual team members are on the next line)
        team = [member.strip() for member in lines.pop(0).split(',')]  # We're already decoding from windows-1252 codec so we have unicode for names like 'Tanya Pietra\xdf'

        # TODO: implement format (units!), instrument correction(s)
        dec_fmt_corr = lines.pop(0)
        declination, fmt, corrections, corrections2 = CompassSurveyParser._parse_declination_line(dec_fmt_corr)

        lines.pop(0)
        shot_header = lines.pop(0).split()
        val_count = len(shot_header) - 2 if 'FLAGS' in shot_header else len(shot_header)  # 1998 vintage data has no FLAGS, COMMENTS at end
        lines.pop(0)

        survey = Survey(name=name, date=date, comment=comment, team=team, cave_name=cave_name,
                        shot_header=shot_header, declination=declination,
                        file_format=fmt, corrections=corrections, corrections2=corrections2)

        shots = []
        shot_lines = lines
        for shot_line in shot_lines:
            shot_vals = shot_line.split(None, val_count)

            if len(shot_vals) > val_count:  # last two spare columns are FLAGS and COMMENTS, either value may be missing
                flags_comment = shot_vals.pop()
                if not flags_comment.startswith('#|'):
                    flags, comment = '', flags_comment
                else:
                    try:
                        flags, comment = flags_comment.split('#|', 1)[1].split('#', 1)
                    except ValueError:
                        raise ParseException('Invalid flags in %s survey: %s' % (name, flags_comment))  # A 2013 bug in Compass inserted corrupt binary garbage into FLAGS column, causes parse to barf
                shot_vals += [flags, comment.strip()]

            shot_vals = [(header, self._coerce(header, val)) for (header, val) in zip(shot_header, shot_vals)]
            shot = Shot(shot_vals)
            survey.add_shot(shot)

        #log.debug("Survey: name=%s shots=%d length=%0.1f date=%s team=%s\n%s", name, len(shots), survey.length, date, team, '\n'.join([str(shot) for shot in survey.shots]))

        return survey


class CompassDatParser(object):
    """Parser for Compass .DAT data files"""

    def __init__(self, datfilename):
        """:param datfilename: (string) filename"""
        self.datfilename = datfilename

    def parse(self):
        """Parse our data file and return a :class:`DatFile` or raise :exc:`ParseException`."""
        log.debug("Parsing Compass .DAT file %s ...", self.datfilename)
        datobj = DatFile(name_from_filename(self.datfilename), filename=self.datfilename)

        with codecs.open(self.datfilename, 'rb', 'windows-1252') as datfile:
            full_contents = datfile.read()
            survey_strs = [survey_str.strip() for survey_str in full_contents.split('\x0C')]

            if survey_strs[-1] == '\x1A':
                survey_strs.pop()  # Compass may place a "soft EOF" with ASCII SUB char

            log.debug("Parsed %d raw surveys from Compass .DAT file %s.", len(survey_strs), self.datfilename)
            for survey_str in survey_strs:
                if not survey_str:
                    continue
                survey = CompassSurveyParser(survey_str).parse()
                datobj.add_survey(survey)

        return datobj


class CompassProjectParser(object):
    """Parser for Compass .MAK project files."""

    def __init__(self, projectfile):
        """:param projectfile: (string) filename"""
        self.makfilename = projectfile

    def parse(self):
        """Parse our project file and return :class:`Project` object or raise :exc:`ParseException`."""
        log.debug("Parsing Compass .MAK file %s ...", self.makfilename)

        base_location = None
        linked_files = []
        file_params = set()

        def parse_linked_file(value):
            log.debug("Parsing linked file:  %s", value)
            value = value.rstrip(';')
            toks = value.split(',', 1)
            if len(toks) == 1:
                return toks[0]
            else:
                return toks[0]  # TODO: implement link stations and fixed stations

        with codecs.open(self.makfilename, 'rb', 'windows-1252') as makfile:
            prev = None

            for line in makfile:
                line = line.strip()

                if not line:
                    continue

                header, value = line[0], line[1:]

                if prev:
                    if line.endswith(';'):
                        linked_file = parse_linked_file(prev + line.rstrip(';'))
                        linked_files.append(linked_file)
                        prev = None
                    else:
                        prev += value
                    continue

                if header == '/':
                    pass  # comment

                elif header == '@':
                    value = value.rstrip(';')
                    base_location = UTMLocation(*(float(v) for v in value.split(',')))

                elif header == '&':
                    value = value.rstrip(';')
                    base_location.datum = value

                elif header == '%':
                    value = value.rstrip(';')
                    base_location.convergence = float(value)

                elif header == '!':
                    value = value.rstrip(';')
                    #file_params = set(value)  # TODO

                elif header == '#':
                    if value.endswith(';'):
                        linked_files.append(parse_linked_file(value))
                        prev = None
                    else:
                        prev = value

            log.debug("Project:  base_loc=%s  linked_files=%s", base_location, linked_files)

            project = Project(name_from_filename(self.makfilename), filename=self.makfilename)
            project.set_base_location(base_location)

            for linked_file in linked_files:
                # TODO: we need to support case-insensitive path resolution on case-sensitive filesystems
                linked_file_path = os.path.join(os.path.dirname(self.makfilename), os.path.normpath(linked_file.replace('\\', '/')))
                datfile = CompassDatParser(linked_file_path).parse()
                project.add_linked_file(datfile)

            return project
