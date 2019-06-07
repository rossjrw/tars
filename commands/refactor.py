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
        cls.has_refactored = True
        refactor_database(irc_c)

    @staticmethod
    def refactor_database(irc_c):
        """Query is executed as script"""
        irc_c.db._driver.issue("""
            ALTER TABLE user_aliases
            ADD COLUMN most_recent_irc BOOLEAN NOT NULL
                CHECK (most_recent_irc IN (0,1))
                DEFAULT 0
                               """)
