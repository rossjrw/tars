"""parsemessages

Plugin that parses messages into commands and then does stuff
"""

from helpers import parse
import commands
from pyaib.plugins import observe, plugin_class
import sys
import inspect

COMMANDS = {
    "search": { "func": search },
    "test": { "func": search },
    "die": { "func": search },
    "chevron": { "func": search },
    "colour": { "func": colour },
}

@plugin_class("parsemessages")
class ParseMessages(object):
    def __init__(self, irc_c, config):
        print("Parse plugin loaded!")
        # The config is conf's plugin.parse
        # TODO generate COMMANDS from commands folder
        self.COMMANDS = {}
        for name,obj in inspect.getmembers(commands):
            if inspect.isclass(obj):
                print(name,obj)

    @observe("IRC_MSG_PRIVMSG")
    def handleMessage(self, irc_c, msg):
        print("Handling message: " + msg.message)
        cmd = parse.command(msg.message)
        # cmd is the parsed msg (used to be msg.parsed)
        if cmd.command in COMMANDS:
            # this is a command!
            msg.reply("That's the " + cmd.command.upper() + " command")
            for tag in cmd.arguments:
                msg.reply(tag + ": " + ", ".join(cmd.arguments[tag]))
            for command in COMMANDS:
                if cmd.command == command:
                    COMMANDS[command]["func"](irc_c, msg, cmd)
        elif cmd.pinged:
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
    msg.reply(parse.nickColor(msg.message))

def search(irc_c, msg, cmd):
    pass

