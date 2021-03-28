"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen, and
also for checking user permissions.
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
    # If there is no command string, there's no need to defer
    if cmd.command is None:
        return False
    # If the bot was pinged, forget everything else - this command is happening
    if cmd.ping:
        return False
    # Filter the deferral configs by the bots that are currently present
    members = DB.get_channel_members(cmd.channel)
    defer_configs = [
        config
        for config in CONFIG['deferral']
        if config['name'] in members
        and config['name'] != CONFIG['nick']
        and config['prefix'] == cmd.prefix
    ]
    # Check if this command has the same name as any matching commands
    if any(
        cmd.command.lower()
        in [command.lower() for command in config['commands']]
        for config in defer_configs
    ):
        return True
    return False


def deferred_bots_for_alias(alias):
    """Returns a dict where the keys are bot names whose commands have an alias
    that conflicts with the provided alias, and the values are a list of
    prefixes that would cause that conflict."""
    return {
        # TODO Support more prefixes than one
        config['name']: [config['prefix']]
        for config in CONFIG['deferral']
        if alias.lower() in config['commands']
    }


def is_controller(cmd):
    """Checks if the sender of the given command is a bot controller.

    Avoid using this if possible. Prefer defining permission levels on commands
    and arguments. Only use this if finer control is needed (e.g. if the
    permission level depends on the value of an argument).
    """
    return cmd.sender in DB.get_controllers()


def get_users(irc_c, channel):
    """Issues a NAMES request to the IRC server for the given channel."""
    irc_c.RAW("NAMES {}".format(channel))


def make_permission_checker(cmd):
    """Constructs and returns a function that will check if the current IRC
    context matches the provided permission level."""
    # The permission level can currently either be True or False
    def permission_checker(permission_level):
        if permission_level:
            return is_controller(cmd)
        return True

    return permission_checker
