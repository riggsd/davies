"""
davies.math: basic mathematics routines for reduction of survey data

This is "slow math", operating on scalar values without vector math (no `numpy` dependency).
"""

import math


__all__ = 'hd', 'vd', 'cartesian_offset', 'angle_delta', \
          'm2ft', 'ft2m'


#
# Unit Conversions
#

def m2ft(m):
    """Convert meters to feet"""
    return m * 3.28084

def ft2m(ft):
    """Convert feet to meters"""
    return ft * 0.3048


#
# Trig Routines
#

def hd(inc, sd):
    """
    Calculate horizontal distance.

    :param inc: (float) inclination angle in degrees
    :param sd:  (float) slope distance in any units
    """
    return sd * math.cos(math.radians(inc))


def vd(inc, sd):
    """
    Calculate vertical distance.

    :param inc: (float) inclination angle in degrees
    :param sd:  (float) slope distance in any units
    """
    return abs(sd * math.sin(math.radians(inc)))


def cartesian_offset(azm, inc, sd, origin=(0, 0)):
    """
    Calculate the (X, Y) cartesian coordinate offset.

    :param azm:    (float) azimuth angle in degrees
    :param inc:    (float) inclination angle in degrees
    :param sd:     (float) slope distance in any units
    :param origin: (tuple(float, float)) optional origin coordinate
    """
    hd = sd * math.cos(math.radians(inc))
    x = hd * math.sin(math.radians(azm))
    y = hd * math.cos(math.radians(azm))
    return (x, y) if not origin else (x+origin[0], y+origin[1])


def angle_delta(a1, a2):
    """
    Calculate the absolute difference between two angles in degrees

    :param a1: (float) angle in degrees
    :param a2: (float) angle in degrees
    """
    return 180 - abs(abs(a1 - a2) - 180)
