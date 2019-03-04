"""parsemessages

Plugin that parses messages into commands and then does stuff
"""

from . import parse
from pyaib.plugins import observe, plugin_class

COMMANDS = (
    "search",
    "test",
    "die",
    "chevron",
)

@plugin_class("parsemessages")
class ParseMessages(object):
    def __init__(self, irc_c, config):
        print("Parse plugin loaded!")
        # The config is conf's plugin.parse

    @observe("IRC_MSG_PRIVMSG")
    def handleMessage(self, irc_c, msg):
        print("Handling message: " + msg.message)
        msg.parsed = parse.command(msg.message)
        if msg.parsed.command in COMMANDS:
            # this is a command!
            msg.reply("That's the " + msg.parsed.command.upper() + " command")
            pass
        elif msg.parsed.pinged:
            # this isn't a command, but we were pinged
            msg.reply("That's not a valid command.")
        else:
            # not a command, and not pinged
            pass
        if msg.channel is None:
            # we're working in PMs
            pass
        else:
            # we're in a channel
            pass
