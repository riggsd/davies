
import unittest
import datetime

from davies import compass


# Example Compass Project with:
# - NAD83 UTM Zone 13 base location
# - Two imported Data Files
#   - One with 25 cave surveys, four fixed stations
#   - One with 4 surface surveys
TESTFILE = 'test/data/Fulfords.mak'


class CompassParsingTestCase(unittest.TestCase):
	"""In liu of a real test suite, just drive the code by parsing a known file"""

	def runTest(self):
		makparser = compass.CompassProjectParser(TESTFILE)

		project = makparser.parse()
		self.assertEqual(project.name, 'Fulfords')
		self.assertEquals(len(project), 2)

		cave_survey_dat = project.linked_files[0]
		self.assertEqual(cave_survey_dat.name.lower(), 'Fulford'.lower())  # case-insensitive filesystem!
		self.assertEqual(len(cave_survey_dat), 25)
		self.assertTrue('BS' in cave_survey_dat)

		bs_survey = cave_survey_dat['BS']
		self.assertTrue('Stan Allison' in bs_survey.team)
		self.assertEqual(bs_survey.date, datetime.date(1989, 2, 11))
		#self.assertEqual(bs_survey.declination, 11.18)  # TODO: implement declination
		self.assertEqual(len(bs_survey), 15)

		last_shot = bs_survey.shots[-1]
		self.assertEqual(last_shot['FROM'], 'BSA2')
		self.assertEqual(last_shot['TO'], 'BS1')
		self.assertEqual(last_shot['LENGTH'], 37.85)
		self.assertEqual(last_shot['BEARING'], 307.0)
		self.assertEqual(last_shot['INC'], -23.0)
		self.assertEqual(last_shot['LEFT'], float('inf'))
