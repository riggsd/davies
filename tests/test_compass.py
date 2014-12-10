import unittest
import datetime

from davies.compass import *


# Example Compass Project with:
# - NAD83 UTM Zone 13 base location
# - Two imported Data Files
#   - One with 25 cave surveys, four fixed stations
#   - One with 4 surface surveys
TESTFILE = 'tests/data/compass/FULFORDS.MAK'


class CompassParsingTestCase(unittest.TestCase):
    """Parse the sample Compass data and test based on its known values"""

    def setUp(self):
        makparser = CompassProjectParser(TESTFILE)
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
        self.assertEqual(self.shot_w_flags['FLAGS'], 'P')
        self.assertTrue(Exclude.PLOT in self.shot_w_flags.flags)


class CompassSpecialCharacters(unittest.TestCase):

    def runTest(self):
        dat = CompassDatParser('tests/data/compass/unicode.dat').parse()
        for name in dat.surveys[0].team:
            if name.startswith('Tanya'):
                self.assertEqual(name, u'Tanya Pietra\xdf')


class CompassShotCorrection(unittest.TestCase):

    def runTest(self):
        # TODO: add instrument correction
        shot = Shot(declination=8.5)
        shot['BEARING'] = 7.0
        shot['AZM2'] = 189.0
        shot['INC'] = -4
        shot['INC2'] = 3.5
        shot['DIST'] = 15.7

        self.assertEqual(shot.azm, 8.0 + 8.5)
        self.assertEqual(shot.inc, -3.75)


class CompassShotFlags(unittest.TestCase):

    def setUp(self):
        dat = CompassDatParser('tests/data/compass/FLAGS.DAT').parse()
        self.survey = dat['toc']

    def test_comment(self):
        comment_shot = self.survey.shots[8]  # shot toc7-toc7a has flags and comment
        self.assertTrue('Disto' in comment_shot['COMMENTS'])

    def test_no_flags(self):
        shot = self.survey.shots[0]  # shot z23-toc0 has no flags nor comments
        self.assertFalse(Exclude.LENGTH in shot.flags)
        self.assertFalse(Exclude.TOTAL in shot.flags)
        self.assertFalse(shot.flags)
        self.assertTrue(shot.is_included)
        self.assertFalse(shot.is_excluded)

    def test_length_flag(self):
        length_shot = self.survey.shots[8]  # shot toc7-toc7a has 'L' flag
        self.assertTrue(Exclude.LENGTH in length_shot.flags)
        self.assertTrue(length_shot.is_excluded)
        self.assertFalse(length_shot.is_included)

    def test_total_flag(self):
        total_shot = self.survey.shots[13]  # shot toc11-toc11a has 'X' flag
        self.assertTrue(Exclude.TOTAL in total_shot.flags)
        self.assertTrue(total_shot.is_excluded)
        self.assertFalse(total_shot.is_included)

    def test_length_calculations(self):
        survey_len, included_len, excluded_len = 0.0, 0.0, 0.0
        for shot in self.survey:
            survey_len += shot.length
            if Exclude.LENGTH in shot.flags or Exclude.TOTAL in shot.flags:
                excluded_len += shot.length
            else:
                included_len += shot.length
        self.assertEqual(self.survey.length, survey_len)
        self.assertEqual(self.survey.included_length, included_len)
        self.assertEqual(self.survey.excluded_length, excluded_len)
