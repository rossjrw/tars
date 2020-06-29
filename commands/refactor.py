"""refactor.py

TEMPORARY commands for refactoring the database.

- Edit this file to create the required refactor
- Issue .reload
- Issue .refactor

TARS will not allow you to refactor a 2nd time unless you issue .reload again.
"""

from helpers.error import CommandError
from helpers.database import DB
from helpers.defer import defer


class refactor:
    has_refactored = False

    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if cls.has_refactored:
            raise CommandError("Already refactored once this reload.")
        if 'callback' in cmd:
            print(cmd['callback'])
            if cmd['callback'][0] == "msg.reply":
                callback = msg.reply
            else:
                raise CommandError("Unknown callback")
        else:
            callback = None
        try:
            if 'sql' in cmd:
                DB.issue(" ".join(cmd['sql']), callback=callback)
            else:
                refactor.refactor_database(irc_c)
                cls.has_refactored = True
        except:
            msg.reply("Refactoring failed.")
            raise
        msg.reply("Refactoring succeeded.")

    @staticmethod
    def refactor_database(irc_c):
        """Query is NOT executed as script"""
        # DB.issue()
