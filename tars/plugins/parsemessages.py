"""parsemessages.py

Plugin that parses messages into commands and then does stuff
"""

from importlib import reload

from pyaib.plugins import observe, plugin_class

# Import entire commands module so that it can be reloaded
from tars import commands

from tars.helpers import parse
from tars.helpers.config import CONFIG
from tars.helpers.defer import should_defer, make_permission_checker
from tars.helpers.error import (
    CommandError,
    CommandNotExistError,
    CommandParsingError,
    MyFaultError,
    CommandUsageMessage,
)


def try_command(irc_c, msg, cmd, command_name=None):
    """Execute the command of the given name. Returns an int indicating whether
    the command was successful."""
    if command_name is None:
        command_name = cmd.command
    try:
        # Get the command class from the command registry
        try:
            command_class = commands.COMMANDS_REGISTRY.get_command_by_alias(
                command_name
            )
        except KeyError as error:
            raise CommandNotExistError from error
        # Check if the command should defer to another bot
        if should_defer(cmd):
            return 1
        # Construct a function to validate if the user has permission to do
        # something
        permission_checker = make_permission_checker(cmd)
        # Instantiate the command
        command = command_class(permission_checker)
        # Parse the message used to call the command like a command line
        command.parse(cmd.message)
        # Execute the command
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
    except CommandParsingError as error:
        if not command_class.suppress:
            msg.reply(
                "\x02Parsing error:\x0F {}. {}".format(
                    str(error).capitalize(),
                    command_class.make_command_link() if command_class else "",
                ).replace("Unrecognized arguments", "Unrecognised arguments"),
            )
        return 1
    except CommandError as e:
        if not command_class.suppress:
            msg.reply(
                "\x02Invalid command:\x0F {} {}".format(
                    str(e), command.make_command_link() if command else ""
                )
            )
        return 1
    except MyFaultError as e:
        if not command_class.suppress:
            msg.reply("\x02Sorry!\x0F {}".format(str(e)))
        return 1
    except CommandUsageMessage as e:
        if not command_class.suppress:
            msg.reply(str(e))
        return 1
    except Exception as e:
        if msg.raw_channel != CONFIG.channels.home:
            if not command_class.suppress:
                msg.reply(
                    "An unexpected error has occurred. "
                    "I've already reported it — you don't need to "
                    "do anything."
                )
        # need to log the error somewhere - why not #tars?
        irc_c.PRIVMSG(
            CONFIG['channels']['home'],
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
                reload(commands)
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
