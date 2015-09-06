import unittest
import os.path
from datetime import date

from davies.pockettopo import *


DATA_DIR = 'tests/data/pockettopo'

# Example PocketTopo export with:
# - Two surveys
TESTFILE = os.path.join(DATA_DIR, 'tahoma.txt')


class PocketTopoTxtParseTestCase(unittest.TestCase):

    def setUp(self):
        self.txtfile = TxtFile.read(TESTFILE)

    def test_name(self):
        self.assertEqual(self.txtfile.name, 'Tahoma East A')

    def test_units(self):
        self.assertEqual(self.txtfile.length_units, 'feet')
        self.assertEqual(self.txtfile.angle_units, 360)

    def test_len(self):
        self.assertEqual(len(self.txtfile), 2)

    def test_txt_contains(self):
        self.assertTrue('1' in self.txtfile)

    def test_txt_getitem(self):
        self.assertTrue(self.txtfile['1'])

    def test_reference_point(self):
        self.assertEqual(len(self.txtfile.reference_points), 1)
        self.assertTrue('1.0' in self.txtfile.reference_points)
        point = self.txtfile.reference_points['1.0']
        self.assertEqual(point.northing, 5189999.0)
        self.assertTrue(point.comment)

    def test_survey_getitem(self):
        survey = self.txtfile['1']
        self.assertTrue('1.0' in survey)

    def test_survey_date(self):
        survey = self.txtfile['1']
        self.assertEqual(survey.date, date(2015, 6, 22))

    # TODO: ...
