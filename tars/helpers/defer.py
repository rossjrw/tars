"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen.
"""

# jarvis: "Page not found."
# helen: "NICK: I'm sorry, I couldn't find anything."

from tars.helpers.database import DB
from tars.helpers.config import CONFIG


class defer:
    @classmethod
    def check(cls, cmd, *bots):
        """Check whether the given bots are in the channel"""
        # bots should be a list of bot names?
        defer.get_users(cmd.context, cmd.channel)
        if cmd.ping:
            return False
        if cmd.force:
            return False
        members = DB.get_channel_members(cmd.channel)
        return set(members) & set(bots)

    @staticmethod
    def report(cmd, message):
        cmd.context.RAW(
            "PRIVMSG {} {}".format(CONFIG['channels']['home'], message)
        )

    @classmethod
    def controller(cls, cmd):
        """Limit this command only to controllers."""
        return cmd.sender in DB.get_controllers()

    @classmethod
    def get_users(cls, irc_c, channel):
        irc_c.RAW("NAMES {}".format(channel))
