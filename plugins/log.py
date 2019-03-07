"""Log Plugin

Logs all input and output for recordkeeping purposes.
"""

import time
from pyaib.plugins import observe, plugin_class

@plugin_class('log')
class Log:
    def __init__(self, irc_c, config):
        print("Log Plugin Loaded!")

    @observe("IRC_RAW_MSG", "IRC_RAW_SEND")
    def log(self, irc_c, msg):
        print("[{}] <{}> {}".format(
            time.strftime("%H:%M:%S"),
            msg.nick,
            msg.message
        ))
