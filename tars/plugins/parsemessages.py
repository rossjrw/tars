"""parsemessages.py

Plugin that parses messages into commands and then does stuff
"""

from importlib import reload

from pyaib.plugins import observe, plugin_class

import tars.commands

from tars.helpers import parse
from tars.helpers.config import CONFIG
from tars.helpers.error import (
    CommandError,
    CommandNotExistError,
    MyFaultError,
    CommandUsageMessage,
)


def try_command(irc_c, msg, cmd, command_name=None):
    """Execute the command of the given name."""
    if command_name is None:
        command_name = cmd.command
    try:
        # commands are kept in the commands/ module.
        command_class = getattr(tars.commands.COMMANDS, command_name)
        command = command_class(cmd.message)
        command.execute(irc_c, msg, cmd)
        return 0
    except CommandNotExistError:
        if cmd.ping:
            # there are .converse strings for pinged
            return try_command(irc_c, msg, cmd, 'converse')
        if msg.raw_channel is None:
            # should be only in pm
            msg.reply("I don't know what '{}' means.".format(command_name))
            return 1
    except CommandError as e:
        msg.reply("\x02Invalid command:\x0F {}".format(str(e)))
        return 1
    except MyFaultError as e:
        msg.reply("\x02Sorry!\x0F {}".format(str(e)))
        return 1
    except CommandUsageMessage as e:
        msg.reply("\x02Command usage:\x0F {}".format(str(e)))
        return 1
    except Exception as e:
        if msg.raw_channel != CONFIG.channels.home:
            msg.reply(
                "An unexpected error has occurred. "
                "I've already reported it — you don't need to "
                "do anything."
            )
        # need to log the error somewhere - why not #tars?
        irc_c.PRIVMSG(
            "#tars",
            "\x02Error report:\x0F {} issued `{}` → `{}`".format(
                msg.sender, msg.message, e
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
                reload(tars.commands)
            except:
                msg.reply("Reload failed.")
                raise
            else:
                msg.reply("Reload successful.")
            continue
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

    @observe('IRC_MSG_PRIVMSG')
    def handle_message(self, irc_c, msg):
        cmds = parse.parse_commands(irc_c, msg)
        execute_commands(irc_c, msg, cmds)

    @observe('IRC_MSG_INVITE')
    def invited(self, irc_c, msg):
        # TODO check for controller
        irc_c.JOIN(msg.message)
