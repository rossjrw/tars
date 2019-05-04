"""Log Plugin

Logs all input and output for recordkeeping purposes.
"""

import time
from pyaib.plugins import observe, plugin_class
from helpers import parse
from pprint import pprint

@plugin_class('log')
class Log:
    def __init__(self, irc_c, config):
        print("Log Plugin Loaded!")

    @observe('IRC_MSG_PRIVMSG')
    def log(self, irc_c, msg):
        chname = "private" if msg.channel is None else msg.raw_channel
        print("[{}] {} <{}> {}".format(
            time.strftime("%H:%M:%S"),
            parse.nickColor(chname),
            parse.nickColor(msg.nick),
            msg.message
        ))

    @observe('IRC_RAW_SEND')
    def debug(self, irc_c, msg):
        msg = parse.output(msg)
        if not msg:
            return
        print("[{}] --> {}: {}".format(
            time.strftime('%H:%M:%S'),
            parse.nickColor(msg['channel']),
            msg['message']
        ))
