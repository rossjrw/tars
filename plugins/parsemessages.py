"""parsemessages

Plugin that parses messages into commands and then does stuff
"""

from . import parse
from pyaib.plugins import observe, plugin_class

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
            for tag in msg.parsed.arguments:
                msg.reply(tag + ": " + ", ".join(msg.parsed.arguments[tag]))
            for command in COMMANDS:
                if msg.parsed.command == command:
                    COMMANDS[command]["func"](irc_c, msg, msg.parsed)
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

    def colour(irc_c, msg, cmd):
        msg.reply(parse.nickColor(name))

    def search(irc_c, msg, cmd):
        pass
    COMMANDS = {
        "search": { "func": search },
        "test": { "func": search },
        "die": { "func": search },
        "chevron": { "func": search },
        "colour": { "func": colour },
    }
