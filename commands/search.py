"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.basecommand import Base
from helpers.defer import defer

class search(Base):
    @classmethod
    def command(cls, irc_c, msg, cmd):
        defer.check(irc_c, msg, "jarvis")
        msg.reply("I don't know how to search just yet, sorry.")

class regexsearch(Base):
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -x to true
        search.command(cls, irc_c, msg, cmd)

class tags(Base):
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(cls, irc_c, msg, cmd)
