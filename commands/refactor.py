"""refactor.py

TEMPORARY commands for refactoring the database.

- Edit this file to create the required refactor
- Issue .reload
- Issue .refactor

TARS will not allow you to refactor a 2nd time unless you issue .reload again.
"""

from helpers.error import CommandError
from helpers.database import DB

class refactor:
    has_refactored = False
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if cls.has_refactored:
            raise CommandError("Already refactored once this reload.")
        try:
            if cmd.hasarg('sql'):
                DB.issue(" ".join(cmd.getarg('sql')))
            else:
                refactor.refactor_database(irc_c)
                cls.has_refactored = True
        except:
            msg.reply("Refactoring failed.")
            raise
        msg.reply("Refactoring succeeded.")

    @staticmethod
    def refactor_database(irc_c):
        """Query is executed as script"""
        # DB.issue()
        # DB.issue('''
        #     ALTER TABLE messages
        #     ADD COLUMN command BOOLEAN NOT NULL
        #                        CHECK (command IN (0,1))
        #                        DEFAULT 0
        #                        ''')
        # DB.issue('''
        #     UPDATE messages
        #     SET command=1
        #     WHERE message LIKE '.%'
        #                        ''')
