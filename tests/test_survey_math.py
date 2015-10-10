import unittest

from davies.survey_math import *


class MathTestCase(unittest.TestCase):

    def assertSequenceAlmostEqual(self, first, second, places=None, msg=None, delta=None):
        """Fail if the contents of two sequences are not "almost equal"."""
        if first == second:
            return True
        self.assertEqual(len(first), len(second))
        for one, two in zip(first, second):
            self.assertAlmostEquals(one, two, places, msg, delta)


class HorizontalDistanceTest(unittest.TestCase):

    def test1(self):
        self.assertAlmostEqual(hd(0, 100), 100, msg='horizontal distance of a horizontal shot should be 100%')

    def test2(self):
        self.assertAlmostEqual(hd(90, 100), 0, msg='horizontal distance of a plumb-up should be zero')

    def test3(self):
        self.assertAlmostEqual(hd(-90, 100), 0, msg='horizontal distance of a plumb-down should be zero')


class VerticalDistanceTest(unittest.TestCase):

    def test1(self):
        self.assertAlmostEqual(vd(90, 100), 100, msg='vertical distance of a plumb-up should be 100%')

    def test2(self):
        self.assertAlmostEqual(vd(0, 100), 0, msg='vertical distance of a horizontal shot should be zero')

    def test3(self):
        # TODO: or should it be NEGATIVE?!
        self.assertAlmostEqual(vd(-90, 100), 100, msg='vertical distance of a plumb-down should be 100%')


class AngleDeltaTest(unittest.TestCase):

    def test1(self):
        self.assertEqual(angle_delta(359, 0), 1)
        self.assertEqual(angle_delta(0, 359), 1)

    def test2(self):
        self.assertEqual(angle_delta(90, 270), 180)
        self.assertEqual(angle_delta(270, 90), 180)


class CartesianOffsetTest(MathTestCase):
    leg = (100**2/2)**0.5  # pythagorean theorem: leg of 45-deg triangle with hypotenuse of len 100

    def test1(self):
        self.assertSequenceAlmostEqual(cartesian_offset(0, 0, 100), (0, 100), msg='horizontal north')

    def test2(self):
        self.assertSequenceAlmostEqual(cartesian_offset(90, 0, 100), (100, 0), msg='horizontal east')

    def test3(self):
        self.assertSequenceAlmostEqual(cartesian_offset(180, 0, 100), (0, -100), msg='horizontal south')

    def test4(self):
        self.assertSequenceAlmostEqual(cartesian_offset(270, 0, 100), (-100, 0), msg='horizontal west')

    def test5(self):
        self.assertSequenceAlmostEqual(cartesian_offset(0, 90, 100), (0, 0), msg='plumb up')

    def test6(self):
        self.assertSequenceAlmostEqual(cartesian_offset(0, -90, 100), (0, 0), msg='plumb down')

    def test7(self):
        self.assertSequenceAlmostEqual(cartesian_offset(45, 0, 100), (self.leg, self.leg), msg='horizontal at 45azm')

    def test8(self):
        self.assertSequenceAlmostEqual(cartesian_offset(180+45, 0, 100), (-self.leg, -self.leg), msg='horizontal at 125azm')

    def test9(self):
        self.assertSequenceAlmostEqual(cartesian_offset(0, 45, 100), (0, self.leg), msg='high angle north')
