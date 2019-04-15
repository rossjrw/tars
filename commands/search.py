"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.defer import defer
from xmlrpc.client import ServerProxy

class search:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        defer.check(irc_c, msg, "jarvis")


class regexsearch:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -x to true
        search.command(irc_c, msg, cmd)

class tags:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(irc_c, msg, cmd)
