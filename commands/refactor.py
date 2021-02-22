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
    def execute(cls, irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if cls.has_refactored and 'force' not in cmd:
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
        # DB.issue("PRAGMA foreign_keys = 0")
        # # channels_users
        # DB.issue(
        #     '''
        #     ALTER TABLE channels_users
        #     RENAME TO channels_users_bak
        #     '''
        # )
        # DB.issue(
        #     '''
        #     CREATE TABLE channels_users (
        #         channel_id INTEGER NOT NULL
        #             REFERENCES channels(id)
        #             ON DELETE CASCADE
        #             ON UPDATE CASCADE,
        #         user_id INTEGER NOT NULL
        #             REFERENCES users(id)
        #             ON DELETE CASCADE
        #             ON UPDATE CASCADE,
        #         user_mode CHARACTER(1),
        #         date_checked INTEGER NOT NULL
        #             DEFAULT (CAST(STRFTIME('%s','now') AS INT)),
        #         UNIQUE(channel_id, user_id)
        #     )
        #     '''
        # )
        # DB.issue(
        #     '''
        #     INSERT INTO channels_users
        #         ( channel_id, user_id, user_mode, date_checked )
        #     SELECT channel_id, user_id, user_mode, date_checked
        #     FROM channels_users_bak
        #     '''
        # )
        # DB.issue("DROP TABLE channels_users_bak")
        # # user_aliases
        # DB.issue(
        #     '''
        #     ALTER TABLE user_aliases
        #     RENAME TO user_aliases_bak
        #     '''
        # )
        # DB.issue(
        #     '''
        #     CREATE TABLE user_aliases (
        #         user_id INTEGER NOT NULL
        #             REFERENCES users(id)
        #             ON DELETE CASCADE
        #             ON UPDATE CASCADE,
        #         alias TEXT NOT NULL
        #             COLLATE NOCASE,
        #         type TEXT NOT NULL
        #             CHECK (type IN ('irc','wiki','discord')),
        #         most_recent BOOLEAN NOT NULL
        #             CHECK (most_recent IN (0,1))
        #             DEFAULT 0,
        #         weight BOOLEAN NOT NULL
        #             CHECK (weight IN (0,1))
        #             DEFAULT 0,
        #         UNIQUE(user_id, alias, type, weight)
        #     )
        #     '''
        # )
        # DB.issue(
        #     '''
        #     INSERT INTO user_aliases
        #         ( user_id, alias, type, most_recent, weight )
        #     SELECT user_id, alias, type, most_recent, weight
        #     FROM user_aliases_bak
        #     '''
        # )
        # DB.issue("DROP TABLE user_aliases_bak")
        # # messages
        # DB.issue(
        #     '''
        #     ALTER TABLE messages
        #     RENAME TO messages_bak
        #     '''
        # )
        # DB.issue(
        #     '''
        #     CREATE TABLE messages (
        #         id INTEGER PRIMARY KEY,
        #         channel_id INTEGER
        #             REFERENCES channels(id)
        #             ON DELETE CASCADE
        #             ON UPDATE CASCADE,
        #         kind TEXT NOT NULL
        #             DEFAULT 'PRIVMSG',
        #         sender TEXT NOT NULL
        #             COLLATE NOCASE,
        #         command BOOLEAN NOT NULL
        #             CHECK (command IN (0,1))
        #             DEFAULT 0,
        #         timestamp INTEGER NOT NULL,
        #         message TEXT NOT NULL,
        #         ignore BOOLEAN NOT NULL
        #             CHECK (ignore IN (0,1))
        #             DEFAULT 0
        #     )
        #     '''
        # )
        # DB.issue(
        #     '''
        #     INSERT INTO messages
        #         ( id, channel_id, kind, sender, command, timestamp, message, ignore )
        #     SELECT id, channel_id, kind, sender, command, timestamp, message, ignore
        #     FROM messages_bak
        #     '''
        # )
        # DB.issue("DROP TABLE messages_bak")
        # # end block
        # DB.issue("PRAGMA foreign_keys = 1")
