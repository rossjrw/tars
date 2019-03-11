"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.basecommand import Base

class search(Base):
    aliases = ["sea", "s"]
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("I don't know how to search just yet, sorry.")
    @classmethod
    def test(cls):
        print("SSEARCH TEST SEARCH TEST SEARCH TEST SEARCH TETEST")

class regexsearch(Base):
    aliases = ["rsea", "rsearch", "rs"]
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -x to true
        search.command(cls, irc_c, msg, cmd)

class tags(Base):
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(cls, irc_c, msg, cmd)
