"""
Davies: Python library for cave survey data
"""

import os.path
import logging
from datetime import datetime

log = logging.getLogger(__name__)


# Compass OO Model


class Survey(object):

	def __init__(self, name=None, date=None, comment=None, team=None, declination=None, lrud_format=None, corrections=None, cave_name=None, shot_header=None, shots=None):
		self.name = name
		self.date = date
		self.comment = comment
		self.team = team
		self.declination = declination
		self.lrud_format = lrud_format
		self.corrections = corrections
		self.cave_name = cave_name
		self.shot_header = shot_header
		self.shots = shots if shots else []

	def add_shot(self, shot):
		self.shots.append(shot)

	@property
	def length(self):
		return sum([shot['LENGTH'] for shot in self.shots])

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


class DatFile(object):

	def __init__(self, name=None):
		self.name = name
		self.surveys = []

	def add_survey(self, survey):
		self.surveys.append(survey)

	def __len__(self):
		return len(self.surveys)

	def __iter__(self):
		for survey in self.surveys:
			yield survey

	def __contains__(self, item):
		for survey in self.surveys:
			if item == survey.name:
				return True
		return False


class UTMLocation(object):

	def __init__(self, easting, northing, elevation, zone=None, convergence=None, datum=None):
		self.easting = easting
		self.northing = northing
		self.elevation = elevation
		self.zone = int(zone) if zone is not None else None
		self.convergence = convergence
		self.datum = datum

	def __str__(self):
		return "<%s UTM Zone %s %0.1fE %0.1fN %0.1f>" % (self.datum, self.zone, self.easting, self.northing, self.elevation)


class Project(object):

	def __init__(self, name=None, base_location=None, file_params=None):
		self.name = name
		self.base_location = base_location
		self.file_params = file_params
		self.linked_files = []

	def add_linked_file(self, datfile):
		self.linked_files.append(datfile)

	def __len__(self):
		return len(self.linked_files)

	def __iter__(self):
		for linked_file in self.linked_files:
			yield linked_file


# File Parsing Utilities


def name_from_filename(fname):
	return os.path.splitext(os.path.basename(fname))[0].replace('_', ' ')


class ParseException(Exception):
	pass


class CompassSurveyParser(object):

	def __init__(self, survey_str):
		self.survey_str = survey_str

	_FLOAT_KEYS = ['LENGTH', 'BEARING', 'AZM2', 'INC', 'INC2', 'LEFT', 'RIGHT', 'UP', 'DOWN']
	_INF_KEYS = ['LEFT', 'RIGHT', 'UP', 'DOWN']

	@staticmethod
	def _coerce(key, val):
		if val == '-999.00':  # no data
			return None

		if key in CompassSurveyParser._INF_KEYS and val == '-9.90':  # passage
			return float('inf')

		if key in CompassSurveyParser._FLOAT_KEYS:
			try:
				return float(val)
			except TypeError as e:
				log.warn("Unable to coerce to float %s=%s (%s)", key, val, type(val))

		return val

	def parse(self):
		if not self.survey_str:
			return None
		lines = self.survey_str.splitlines()
		if len(lines) < 10:
			raise ParseException("Expected at least 10 lines in a Compass Survey, only found %d!\nlines=%s" % (len(lines), lines))

		cave_name = lines.pop(0).strip()
		name = lines.pop(0).split('SURVEY NAME:', 1)[1].strip()
		date, comment = lines.pop(0).split('SURVEY DATE:', 1)[1].split('COMMENT:')
		date = datetime.strptime(date.strip(), '%m %d %Y').date()

		lines.pop(0)  # SURVEY TEAM:\n
		team = [member.strip() for member in lines.pop(0).split(',')]

		dec_fmt_corr = lines.pop(0)  # TODO: implement declination, format, instrument correction(s)

		lines.pop(0)
		shot_header = lines.pop(0).split()
		lines.pop(0)

		survey = Survey(name=name, date=date, comment=comment, team=team, cave_name=cave_name, shot_header=shot_header)

		# TODO: for now, let's totally ignore flags and comments
		shot_header = shot_header[:-2]
		shots = []
		shot_lines = lines
		for shot_line in shot_lines:
			shot_vals = shot_line.split(None, len(shot_header))[:len(shot_header)]
			shot = dict(zip(shot_header, shot_vals))
			shot = {k:self._coerce(k,v) for (k,v) in shot.items()}
			survey.add_shot(shot)

		log.debug("Survey: name=%s shots=%d length=%0.1f date=%s team=%s\n%s", name, len(shots), survey.length, date, team, '\n'.join([str(shot) for shot in survey.shots]))

		return survey


class CompassDatParser(object):

	def __init__(self, datfilename):
		self.datfilename = datfilename

	def parse(self):
		log.debug("Parsing Compass .DAT file %s ...", self.datfilename)
		datobj = DatFile(name_from_filename(self.datfilename))

		with open(self.datfilename, 'rb') as datfile:
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

	def __init__(self, projectfile):
		self.makfilename = projectfile

	def parse(self):
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

		with open(self.makfilename, 'rb') as makfile:
			prev = None

			for line in makfile:
				line = line.strip()

				if not line:
					continue

				if prev:
					if line.endswith(';'):
						linked_files.append( parse_linked_file(prev + line.rstrip(';')) )
						prev = None
					else:
						prev += value
					continue

				header, value = line[0], line[1:]

				if header == '/':
					pass  # comment

				elif header == '@':
					value = value.rstrip(';')
					base_location = UTMLocation( *(float(v) for v in value.split(',')) )

				elif header == '&':
					value = value.rstrip(';')
					base_location.datum = value

				elif header == '%':
					value = value.rstrip(';')
					base_location.convergence = float(value)

				elif header == '!':
					value = value.rstrip(';')
					file_params = set(value.upper())

				elif header == '#':
					if value.endswith(';'):
						linked_files.append( parse_linked_file(value) )
						prev = None
					else:
						prev = value

			log.debug("Project:  base_loc=%s  params=%s  linked_files=%s", base_location, file_params, linked_files)

			project = Project(name_from_filename(self.makfilename), base_location, file_params)

			for linked_file in linked_files:
				linked_file_path = os.path.join(os.path.dirname(self.makfilename), os.path.normpath(linked_file.replace('\\', '/')))
				datfile = CompassDatParser(linked_file_path).parse()
				project.add_linked_file(datfile)

			return project
