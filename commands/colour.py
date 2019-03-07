from helpers import parse

class colour:
    @classmethod
    def command(irc_c, msg, cmd):
        msg.reply(parse.nickColor(msg.message))
