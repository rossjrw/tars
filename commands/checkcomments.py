"""checkcomments.py

Checks your posts for replies you may have missed.
"""


class checkcomments:
    """Checks for new comments."""

    @staticmethod
    def command(irc_c, msg, cmd):
        cmd.expandargs(["author a"])
