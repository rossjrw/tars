"""parsemessages.py

Plugin that parses messages into commands and then does stuff
"""

from helpers import parse
import commands
from pyaib.plugins import observe, plugin_class
import sys
import inspect
from helpers.error import CommandError, CommandNotExistError, MyFaultError
from importlib import reload
from pprint import pprint
import time

def try_command(attempt, irc_c, msg, cmd):
    try:
        # Call the command from the right file in commands/
        # getattr instead of commands[cmd] bc module subscriptability
        command_class = getattr(commands.COMMANDS, attempt)
        command_class.command(irc_c, msg, cmd)
    except CommandNotExistError:
        if cmd.pinged:
            # there are .converse strings for pinged
            try_command('converse', irc_c, msg, cmd)
        elif msg.channel is None:
            # should be only in pm
            msg.reply("That's not a command.")
    except CommandError as e:
        msg.reply("\x02Invalid command:\x0F {}".format(str(e)))
    except MyFaultError as e:
        msg.reply("\x02Sorry!\x0F {}".format(str(e)))
    except Exception as e:
        if msg.channel != '#tars':
            msg.reply(("An unexpected error has occurred. "
                       "I've already reported it — you don't need to "
                       "do anything."))
        # need to log the error somewhere - why not #tars?
        irc_c.PRIVMSG("#tars",("\x02Error report:\x0F {} "
                               "issued `{}` → `{}`"
                              .format(msg.sender,msg.message,e)))
        raise

@plugin_class('parsemessages')
class ParseMessages():
    def __init__(self, irc_c, config):
        print("Parse plugin loaded!")

# TODO: if plugins are just object instances, then we should be able to
# wipe em and remake em to .reload
    @observe("IRC_MSG_PRIVMSG")
    def handleMessage(self, irc_c, msg):
        cmd = parse.ParsedCommand(irc_c, msg)
        # cmd is the parsed msg (used to be msg.parsed)
        if cmd.command:
            # this is a command!
            if cmd.command == "reload":
                # special case for .reload - needs high priority
                msg.reply("Reloading commands...")
                try:
                    reload(commands)
                except:
                    msg.reply("Reload failed.")
                    raise
                else:
                    msg.reply("Reload successful.")
                return
            # notify of a shlex error, if present
            if cmd.quote_error:
                msg.reply(("I wasn't able to correctly parse your quotemarks, "
                           "so I have interpreted them literally."))
            try_command(cmd.command, irc_c, msg, cmd)
        else:
            # not a command, and not pinged
            # Send the message over to .converse
            try_command('converse', irc_c, msg, cmd)
        if msg.channel is None:
            # we're working in PMs
            pass
        else:
            # we're in a channel
            pass

    @observe('IRC_MSG_INVITE')
    def invited(self, irc_c, msg):
        # TODO check for controller
        irc_c.JOIN(msg.message)
