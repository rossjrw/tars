from ..helpers import parse

class colour:
    @staticmethod
    def call(irc_c, msg, cmd):
        msg.reply(parse.nickColor(msg.message))
