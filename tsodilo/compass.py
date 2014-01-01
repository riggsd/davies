"""
Tsodillo: Python library for cave survey data
"""

from datetime import datetime

import logging
log = logging.getLogger(__name__)


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
		self.shots = shots

	def add_shot(self, shot):
		if not self.shots:
			self.shots = []
		self.shots.append(shot)

	@property
	def length(self):
		if not self.shots:
			return 0
		return sum([shot['LENGTH'] for shot in self.shots])


class ParseException(Exception):
	pass


class CompassSurveyParser(object):

	def __init__(self, survey_str):
		self.survey_str = survey_str

	_FLOAT_KEYS = ['LENGTH', 'BEARING', 'AZM2', 'INC', 'INC2', 'LEFT', 'RIGHT', 'UP', 'DOWN']

	@staticmethod
	def _coerce(key, val):
		if val == '-999.00':
			return None
		if key in CompassSurveyParser._FLOAT_KEYS:
			try:
				return float(val)
			except TypeError, e:
				log.warn("Unable to coerce to float %s=%s (%s)", key, val, type(val))
				raise e
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
			shot = {k:self._coerce(k,v) for (k,v) in shot.iteritems()}
			survey.add_shot(shot)

		log.debug("Survey: name=%s shots=%d length=%0.1f date=%s team=%s\n%s", name, len(shots), survey.length, date, team, '\n'.join([str(shot) for shot in survey.shots]))

		return survey


class CompassDatParser(object):

	def __init__(self, datfile):
		self.datfilename = datfile

	def parse(self):
		log.debug("Parsing Compass .DAT file %s ...", self.datfilename)
		surveys = []

		with open(self.datfilename, 'rb') as datfile:
			full_contents = datfile.read()
			survey_strs = [survey_str.strip() for survey_str in full_contents.split('\x0C')]

			if survey_strs[-1] == '\x1A':
				survey_strs.pop()  # Compass may place a "soft EOF" with ASCII SUB char

			log.debug("Parsed %d raw surveys from Compass .DAT file %s.", len(survey_strs), self.datfilename)
			for survey_str in survey_strs:
				survey = CompassSurveyParser(survey_str).parse()
				if survey:
					surveys.append(survey)

		return surveys

