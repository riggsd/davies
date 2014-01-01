Tsodilo
-------

Tsodilo is a pure-Python package for manipulating cave survey data.

It is currently in a very, very early phase of development, and should be considered a "proof of concept" implementation.


Current support includes:

 - Parsing of `Compass <http://www.fountainware.com/compass/>`_ source files

 - That's it!


Example usage::

  from tsodilo import compass

  # Parse a .DAT file
  parser = compass.CompassDatParser('mycave.dat')
  surveys = parser.parse()

  print len(surveys)
  >> 17

  survey = surveys[0]

  print survey.name
  >> A

  print survey.date
  >> 2006-09-30

  print survey.shots[0]
  >> {'FROM': 'A1', 'TO': 'A2', 'LENGTH': 16.8, 'BEARING': 158.0, 'INC': -30.0, 'LEFT': 12.0, 'RIGHT': 15.0, 'UP': 15.0, 'DOWN': 20.0 }

  print survey.length
  >> 384.7


Or a more useful example, which shows who has surveyed the most footage in your project::

    from tsodilo import compass

    cavers = {}

    for datfile in sys.argv[1:]:
        for survey in compass.CompassDatParser(datfile).parse():
            for member in survey.team:
                cavers[member] = cavers.get(member, 0.0) + survey.length

    for name in sorted(cavers, key=cavers.get, reverse=True):
        print "%s:\t%0.1f" % (name, cavers[name])


The name "Tsodilo" is a nod to the `Tsodilo Hills UNESCO World Heritage Site <http://whc.unesco.org/en/list/1021>`_ in
Botswana, which features a remote cave housing a large python-shaped rock which has been visited by humans for more than
70,000 years.


Tsodilo is Open Source software licensed under the MIT License, and is copyright (C) Myotisoft LLC.
