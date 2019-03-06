"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

class search:
    aliases = ["sea", "s"]
    @classmethodd
    def command(irc_c, msg, cmd):
        msg.reply("I don't know how to search just yet, sorry.")

class regexsearch:
    aliases = ["rsea", "rsearch", "rs"]
    @classmethodd
    def command(irc_c, msg, cmd):
        # TODO set -x to true
        search.command(irc_c, msg, cmd)

class tags:
    @classmethodd
    def command(irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(irc_c, msg, cmd)
