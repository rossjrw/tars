"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen.
"""

# jarvis: "Page not found."
# helen: "NICK: I'm sorry, I couldn't find anything."

from tars.helpers.database import DB
from tars.helpers.config import CONFIG


def should_defer(cmd):
    """Evaluates whether or not a given command should execute. Returns True if
    the command should defer. Returns False if the command should not defer,
    i.e. it is okay to execute.

    The command does not execute if the prefix and alias are shared by another
    bot, unless the bot was pinged.
    """
    # If there is no command string, what?
    if cmd.command is None:
        raise ValueError("command is None")
    # If the bot was pinged, forget everything else - this command is happening
    if cmd.ping:
        return False
    # Filter the deferral configs by the bots that are currently present
    members = DB.get_channel_members(cmd.channel)
    defer_configs = [
        config
        for config in CONFIG['deferral']
        if config['name'] in members and config['prefix'] == cmd.prefix
    ]
    # Check if this command has the same name as any matching commands
    if any(
        cmd.command.lower() in [command.lower() for command in config.commands]
        for config in defer_configs
    ):
        return True
    return False


def is_controller(cmd):
    """Limit this command only to controllers."""
    return cmd.sender in DB.get_controllers()


def get_users(irc_c, channel):
    irc_c.RAW("NAMES {}".format(channel))
