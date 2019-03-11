"""basecommand.py

Base class from which all commnads inherit.
"""

class Base:
    all_aliases = {}

    def test(self):
        print("{} TEST TEST TEST".format(self.__class__.__name__))
