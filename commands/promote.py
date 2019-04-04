"""promote.py

Commands for IO to use to promote articles across social media.
"""

from tomlkit import loads
from tomlkit import dumps

class promote:
    """Base command, reliant on config"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        pass
