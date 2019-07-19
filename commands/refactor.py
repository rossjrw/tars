"""refactor.py

TEMPORARY commands for refactoring the database.

- Edit this file to create the required refactor
- Issue .reload
- Issue .refactor

TARS will not allow you to refactor a 2nd time unless you issue .reload again.
"""

from helpers.error import CommandError

class refactor:
    has_refactored = False
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if msg.nick != "Croquembouche":
            raise CommandError("Only Croquembouche can do that.")
        if cls.has_refactored:
            raise CommandError("Already refactored once this reload.")
        try:
            if cmd.hasarg('sql'):
                irc_c.db._driver.issue(" ".join(cmd.getarg('sql')))
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
        # irc_c.db._driver.issue()
        # irc_c.db._driver.issue('''
        #     ALTER TABLE messages
        #     ADD COLUMN command BOOLEAN NOT NULL
        #                        CHECK (command IN (0,1))
        #                        DEFAULT 0
        #                        ''')
        # irc_c.db._driver.issue('''
        #     UPDATE messages
        #     SET command=1
        #     WHERE message LIKE '.%'
        #                        ''')
