# Searches the wiki database per the search parameters.

class search:
    @staticmethod
    def command(irc_c, msg, cmd):
        msg.reply("I don't know how to search just yet, sorry.")

class regexsearch:
    @staticmethod
    def command(irc_c, msg, cmd):
        # TODO set -x to true
        search.command(irc_c, msg, cmd)

class tags:
    @staticmethod
    def command(irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(irc_c, msg, cmd)
