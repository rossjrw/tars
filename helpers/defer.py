"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen.
"""

# jarvis: "Page not found."
# helen: "NICK: I'm sorry, I couldn't find anything."

from helpers.database import DB
from helpers.config import CONFIG

class defer:
    @classmethod
    def check(cls, msg, *bots):
        """Check whether the given bots are in the channel"""
        # bots should be a list of bot names?
        members = DB.get_channel_members(msg.channel)
        return set(members) & set(bots)

    @classmethod
    def controller(cls, cmd):
        """Limit this command only to controllers."""
        return cmd.sender in DB.get_controllers()
