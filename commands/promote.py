"""promote.py

Commands for IO to use to promote articles across social media.
"""

from tomlkit import loads
from tomlkit import dumps

from helpers.basecommand import Command


class Promote(Command):
    """Base command, reliant on config"""

    def execute(self, irc_c, msg, cmd):
        pass
