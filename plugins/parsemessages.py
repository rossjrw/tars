"""parsemessages.py

Plugin that parses messages into commands and then does stuff
"""

import commands
from importlib import reload
from pyaib.plugins import observe, plugin_class
from helpers import parse
from helpers.error import CommandError, CommandNotExistError, MyFaultError


def try_command(irc_c, msg, cmd, command_name=None):
    """Execute the command of the given name."""
    if command_name is None:
        command_name = cmd.command
    try:
        # Call the command from the right file in commands/
        # getattr instead of commands[cmd] bc module subscriptability
        command_class = getattr(commands.COMMANDS, command_name)
        command_class.command(irc_c, msg, cmd)
        return 0
    except CommandNotExistError:
        if cmd.pinged:
            # there are .converse strings for pinged
            return try_command('converse', irc_c, msg, cmd)
        elif msg.raw_channel is None:
            # should be only in pm
            msg.reply("I don't know what '{}' means.".format(command_name))
            return 1
    except CommandError as exc:
        msg.reply("\x02Invalid command:\x0F {}".format(str(exc)))
        return 1
    except MyFaultError as exc:
        msg.reply("\x02Sorry!\x0F {}".format(str(exc)))
        return 1
    except Exception as exc:
        if msg.raw_channel != '#tars':
            msg.reply(
                (
                    "An unexpected error has occurred. "
                    "I've already reported it — you don't need to "
                    "do anything."
                )
            )
        # need to log the error somewhere - why not #tars?
        irc_c.PRIVMSG(
            "#tars",
            (
                "\x02Error report:\x0F {} "
                "issued `{}` → `{}`".format(msg.sender, msg.message, exc)
            ),
        )
        raise


def execute_commands(irc_c, msg, cmds, command_name=None):
    """Executes a series of commands."""
    for cmd in cmds:
        # reload command takes highest priority
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
            continue
        # indiciate quotemark parse error
        if cmd.quote_error:
            msg.reply(
                (
                    "I wasn't able to correctly parse your quotemarks, "
                    "so I have interpreted them literally."
                )
            )
        # assume converse if no command specified
        if not cmd.command:
            command_name = 'converse'
        # do not catch error if this fails
        command_failed = try_command(irc_c, msg, cmd, command_name)
        # only progress to next command if previous passed
        if command_failed:
            break


@plugin_class('parsemessages')
class ParseMessages:
    def __init__(self, irc_c, config):
        print("Parse plugin loaded!")

    # TODO: if plugins are just object instances, then we should be able to
    # wipe em and remake em to .reload
    @observe("IRC_MSG_PRIVMSG")
    def handle_message(self, irc_c, msg):
        cmds = parse.parse_commands(irc_c, msg)
        execute_commands(irc_c, msg, cmds)

    @observe('IRC_MSG_INVITE')
    def invited(self, irc_c, msg):
        # TODO check for controller
        irc_c.JOIN(msg.message)
