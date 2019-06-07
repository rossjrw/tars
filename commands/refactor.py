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
        try:
            refactor.refactor_database(irc_c)
        except:
            msg.reply("Refactoring failed.")
            raise
        msg.reply("Refactoring succeeded.")

    @staticmethod
    def refactor_database(irc_c):
        """Query is executed as script"""
        irc_c.db._driver.issue()
        # irc_c.db._driver.issue("""
        #     PRAGMA foreign_keys=OFF;
        #     CREATE TEMPORARY TABLE u_a_bk(user_id,alias,type,most_recent_irc);
        #     INSERT INTO u_a_bk SELECT user_id,alias,type,most_recent_irc
        #                        FROM user_aliases;
        #     DROP TABLE user_aliases;
        #     CREATE TABLE user_aliases(user_id,alias,type,most_recent_irc);
        #     INSERT INTO user_aliases SELECT user_id,alias,type,most_recent_irc
        #                        FROM u_a_bk;
        #     DROP TABLE u_a_bk;
        #     PRAGMA foreign_keys=ON;
        #                        """)
