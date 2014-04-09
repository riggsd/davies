"""
Observer pattern "events" implemented as a decorator.
Based on:  http://stackoverflow.com/a/1926336

Example usage::

    # producer
    class MyJob(object):

        @event
        def progress(pct):
            '''Called when progress is made. pct is the percent complete.'''

        def run(self):
            n = 10
            for i in range(n+1):
                self.progress(100.0 * i / n)

    #consumer
    job = myjobs.MyJob()
    job.progress += lambda pct: sys.stdout.write("%.1f%% done\n" % pct)
    job.run()
"""

__all__ = ['event']


class event(object):
    """
    Event decorator. An event function supports the += and -= operators for
    adding and removing listeners. Directly calling the event fires it.
    """
    def __init__(self, func):
        self.__doc__ = func.__doc__
        self._key = ' ' + func.__name__

    def __get__(self, obj, cls):
        try:
            return obj.__dict__[self._key]
        except KeyError:
            be = obj.__dict__[self._key] = BoundEvent()
            return be


class BoundEvent(object):

    def __init__(self):
        self._fns = []

    def __iadd__(self, fn):
        self._fns.append(fn)
        return self

    def __isub__(self, fn):
        self._fns.remove(fn)
        return self

    def __call__(self, *args, **kwargs):
        for f in self._fns[:]:
            f(*args, **kwargs)
