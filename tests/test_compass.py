
import unittest
import datetime

from davies import compass


# Example Compass Project with:
# - NAD83 UTM Zone 13 base location
# - Two imported Data Files
#   - One with 25 cave surveys, four fixed stations
#   - One with 4 surface surveys
TESTFILE = 'tests/data/compass/FULFORDS.MAK'


class CompassParsingTestCase(unittest.TestCase):
    """Parse the sample Compass data and test based on its known values"""

    def setUp(self):
        makparser = compass.CompassProjectParser(TESTFILE)
        self.project = makparser.parse()
        self.assertTrue(self.project.linked_files, 'Sanity check failed: no linked_files found!')
        self.cave_survey_dat = self.project.linked_files[0]
        self.bs_survey = self.cave_survey_dat['BS']
        self.last_shot = self.bs_survey.shots[-1]
        self.shot_w_flags = self.cave_survey_dat['XS'].shots[0]

    def test_name(self):
        self.assertEqual(self.project.name, 'FULFORDS')

    def test_len(self):
        self.assertEqual(len(self.project), 2)

    def test_dat(self):
        dat = self.cave_survey_dat
        self.assertEqual(dat.name, 'FULFORD')
        self.assertEqual(len(dat), 25)
        self.assertTrue('BS' in dat)

    def test_survey(self):
        survey = self.bs_survey
        self.assertTrue('Stan Allison' in survey.team)
        self.assertEqual(survey.date, datetime.date(1989, 2, 11))
        #self.assertEqual(survey.declination, 11.18)  # TODO: implement declination
        self.assertEqual(len(survey), 15)

    def test_shot(self):
        shot = self.last_shot
        self.assertEqual(shot['FROM'], 'BSA2')
        self.assertEqual(shot['TO'], 'BS1')
        self.assertEqual(shot['LENGTH'], 37.85)
        self.assertEqual(shot['BEARING'], 307.0)
        self.assertEqual(shot['INC'], -23.0)
        self.assertEqual(shot['LEFT'], float('inf'))
        # TODO: this test data doesn't have any COMMENTS

    def test_shot_flags(self):
        shot = self.shot_w_flags
        self.assertEqual(shot['FLAGS'], 'P')


class CompassShotCorrection(unittest.TestCase):

    def runTest(self):
        # TODO: add instrument correction
        shot = compass.Shot(declination=8.5)
        shot['BEARING'] = 7.0
        shot['AZM2'] = 189.0
        shot['INC'] = -4
        shot['INC2'] = 3.5
        shot['DIST'] = 15.7

        self.assertEqual(shot.azm, 8.0 + 8.5)
        self.assertEqual(shot.inc, -3.75)

