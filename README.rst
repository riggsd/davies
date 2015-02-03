Davies
-------

Davies is a Python package for manipulating cave survey data.

It is currently in a very, very early phase of development, and should be considered a "proof of concept" implementation.


Current support includes:

 - Parsing of `Compass <http://www.fountainware.com/compass/>`_ Project (.MAK) and Data (.DAT) source files, as well as
   Plot (.PLT) files.

 - Writing Compass Data (.DAT) files.

 - That's it!


Browse the `Davies API documentation  <http://davies.readthedocs.org>`_


Example usage::

  from davies import compass

  # Parse a .DAT file
  datfile = compass.DatFile.read('MYCAVE.DAT')

  print len(datfile)  # number of surveys in .DAT
  >> 17

  print datfile.length  # total surveyed footage including splays, etc.
  >> 5332.2

  print datfile.included_length  # total surveyed footage after discarding excluded shots
  >> 5280.0

  survey = datfile['BS']  # grab a survey by its survey designation

  print survey.name
  >> A

  print survey.date
  >> 2006-09-30

  print survey.length  # surveyed footage including splays, etc.
  >> 5332.2

  print survey.included_length  # surveyed footage after discarding excluded shots
  >> 5280.0

  print survey.shots[0]
  >> {'FROM': 'A1', 'TO': 'A2', 'LENGTH': 16.8, 'BEARING': 158.0, 'INC': -30.0, 'LEFT': 12.0, 'RIGHT': 15.0, 'UP': 15.0, 'DOWN': 20.0 }

  print survey.shots[0].azm  # azimuth after averaging front and backsights, magnetic declination
  155.2


This example shows who has surveyed the most footage in your project::

    from davies import compass

    cavers = {}

    for datfilename in sys.argv[1:]:
        for survey in compass.DatFile.read(datfilename):
            for member in survey.team:
                cavers[member] = cavers.get(member, 0.0) + survey.length

    for name in sorted(cavers, key=cavers.get, reverse=True):
        print "%s:\t%0.1f" % (name, cavers[name])



Installation
------------

This software requires Python 2.7

Releases are available for installation from the Python Package Index, see
`installation instructions <https://wiki.python.org/moin/CheeseShopTutorial#Installing_Distributions>`_ or simply run
the following command on Mac OS X or most Linux distributions.

``pip install davies``

If you've downloaded a source distribution or checked out from the git repository, install locally with:

``python setup.py install``


Name
----

The name "Davies" is a tribute to `William E. Davies <http://www.aegweb.org/docs/about/william_davies_memorial.pdf>`_,
who pioneered the systematic cave survey of West Virginia and authored *Caverns of West Virginia* in 1949. Bill Davies
later did the statewide cave survey for the state of Maryland, served the roles of President and Vice-President of the
National Speleological Society, and published the definitive US-wide karst map, *Engineering Aspects of Karst*. Davies
still serves as an inspiration today to the cave mappers of West Virginia, of the United States, and the World over.


License
-------

Davies is Open Source software licensed under the MIT License, and is copyright (C) 2013 - 2015 Myotisoft LLC.
