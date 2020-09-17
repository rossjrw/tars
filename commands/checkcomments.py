"""checkcomments.py

Checks your posts for replies you may have missed.
"""

from helpers.database import DB
from helpers.error import CommandError, MyFaultError


class checkcomments:
    """Checks for new comments."""

    @staticmethod
    def command(irc_c, msg, cmd):
        cmd.expandargs(["author a"])
        if 'author' in cmd:
            if len(cmd['author']) < 1:
                raise CommandError(
                    "Specify the name of author whose comments you want to "
                    "check. To check your own, just use .cc with no argument."
                )
            author = " ".join(cmd['author'])
        else:
            user_id = DB.get_user_id(msg.sender)
            author = DB.get_wikiname(user_id)
            if author is None:
                raise MyFaultError(
                    "I don't know your Wikidot username. Let me know what it "
                    "is with .alias --wiki [username]"
                )
