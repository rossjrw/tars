"""Log Plugin

Logs all input and output for recordkeeping purposes.
"""

import time
import sys
from pyaib.plugins import plugin_class
from pyaib.components import observe
from pyaib.signals import emit_signal, await_signal
from tars.helpers import parse
from pprint import pprint
from tars.helpers.database import DB
from tars.helpers.config import CONFIG


def gimmick(message):
    """Detect if a message is the result of a gib gimmick."""
    if message is None:
        return False
    if message.lower().count("oob") > 3:
        return True
    if message.lower().count("ob") > 4:
        return True
    if message.isupper():
        return True
    return False


@plugin_class('log')
class Log:
    banned = False
    print_everything = False

    def __init__(self, irc_c, config):
        print("Log Plugin Loaded!")

    @observe('IRC_RAW_MSG', 'IRC_RAW_SEND')
    def print_all_messages(self, irc_c, msg):
        if Log.banned:
            print(msg)
            sys.exit(1)
        elif Log.print_everything:
            print(msg)

    @observe('IRC_MSG_465')
    def stop_connecting_if_banned(self, irc_c, msg):
        print(msg)
        print("Banned! oh no")
        Log.banned = True

    @observe(
        'IRC_MSG_PRIVMSG',
        'IRC_MSG_NICK',
        'IRC_MSG_JOIN',
        'IRC_MSG_PART',
        'IRC_MSG_QUIT',
    )
    def log(self, irc_c, msg):
        chname = "private" if msg.raw_channel is None else msg.raw_channel
        if msg.kind == 'PRIVMSG':
            print(
                "[{}] {} <{}> {}".format(
                    time.strftime("%H:%M:%S"),
                    parse.nickColor(chname),
                    parse.nickColor(msg.nick),
                    msg.message,
                )
            )
        elif msg.kind == 'NICK':
            print(
                "[{}] {} changed their name to {}".format(
                    time.strftime("%H:%M:%S"),
                    parse.nickColor(msg.nick),
                    parse.nickColor(msg.args),
                )
            )
        else:
            print(
                "[{}] {} {} {}".format(
                    time.strftime("%H:%M:%S"),
                    parse.nickColor(msg.nick),
                    "joined" if msg.kind == 'JOIN' else "left",
                    parse.nickColor(chname),
                )
            )
        try:
            if not gimmick(msg.message):
                DB.log_message(msg)
        except:
            irc_c.RAW("PRIVMSG #tars A logging error has occurred.")
            raise

    @observe('IRC_RAW_SEND')
    def debug(self, irc_c, msg):
        msg = parse.output(msg)
        if not msg:
            return
        print(
            "[{}] --> {}: {}".format(
                time.strftime('%H:%M:%S'),
                parse.nickColor(msg['channel']),
                msg['message'],
            )
        )
        if "IDENTIFY" in msg['message']:
            return
        msg = {
            'channel': msg['channel']
            if msg['channel'].startswith('#')
            else None,
            'sender': CONFIG.nick,
            'kind': "PRIVMSG",
            'message': msg['message'],
            'nick': CONFIG.nick,
            'timestamp': int(time.time()),
        }
        try:
            DB.log_message(msg)
        except:
            irc_c.RAW("PRIVMSG #tars A logging error has occurred.")
            raise
