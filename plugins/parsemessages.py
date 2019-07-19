"""parsemessages.py

Plugin that parses messages into commands and then does stuff
"""

from helpers import parse
import commands
from pyaib.plugins import observe, plugin_class
import sys
import inspect
from helpers.error import CommandError, CommandNotExistError
from importlib import reload
from pprint import pprint

def converse(irc_c, msg, cmd):
    # .converse is used to parse non-command strings
    # we can't always tell if a message is a command or not
    getattr(commands.COMMANDS, 'converse').command(irc_c, msg, cmd)

@plugin_class('parsemessages')
@plugin_class.requires('db')
class ParseMessages(object):
    def __init__(self, irc_c, config):
        print("Parse plugin loaded!")

# TODO: if plugins are just object instances, then we should be able to
# wipe em and remake em to .reload
    @observe("IRC_MSG_PRIVMSG")
    def handleMessage(self, irc_c, msg):
        if msg.message == ".reload":
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
        cmd = parse.command(msg.message)
        # cmd is the parsed msg (used to be msg.parsed)
        if cmd.command:
            # this is a command!
            # notify of a shlex error, if present
            if cmd.quote_error:
                msg.reply(("I wasn't able to correctly parse your quotemarks, "
                           "so I have interpreted them literally."))
            try:
                # Call the command from the right file in commands/
                # getattr instead of commands[cmd] bc module subscriptability
                getattr(commands.COMMANDS, cmd.command).command(irc_c, msg, cmd)
            except CommandNotExistError:
                if cmd.pinged:
                    # there are .converse strings for pinged
                    converse(irc_c, msg, cmd)
                else:
                    msg.reply("That's not a command.")
            except CommandError as e:
                msg.reply("Invalid command: {}".format(str(e)))
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
        else:
            # not a command, and not pinged
            # Send the message over to .converse
            converse(irc_c, msg, cmd)
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
