#!/usr/bin/env python

from distutils.core import setup

from davies import __version__


LONG_DESCRIPTION = open('README.rst').read()


setup(
    name='davies',
    version=__version__,
    author='David A. Riggs',
    author_email='driggs@myotisoft.com',
    url='https://github.com/riggsd/davies',
    description='Package for manipulating cave survey data',
    long_description=LONG_DESCRIPTION,
    packages=['davies', 'davies.compass', 'davies.pockettopo'],
    keywords=['cave', 'survey', 'gis'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
