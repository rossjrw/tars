from ..helpers import parse

class colour:
    def __init__(self, irc_c, msg, cmd):
        msg.reply(parse.nickColor(msg.message))
