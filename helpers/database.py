"""database.py

SQLite3 database driver for TARS.

Plugin responsible for accessing and modifying the database.
ALL database queries MUST pass through this file.
Provides functions for manipulating the database.
"""
# reminder: conn.commit() after making changes (i.e. not queries)
# reminder: 'single quotes' for string literals eg for tables that don't exist

# to access these methods: from a plugin with db marked as required, issue
# irc_c.db._driver.methodname()
# this pretty much bypasses pyaib's db simplifier

from pyaib.db import db_driver
import sqlite3
from pprint import pprint
from helpers.parse import nickColor
import pandas as pd

def dbprint(text, error=False):
    bit = "[\x1b[38;5;108mDatabase\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

def norm(thing):
    """fetchX often returns a tuple or a list of tuples because it's dumb"""
    if thing is None:
        return None
    if all(isinstance(el, (list, tuple)) for el in thing):
        thing = [norm(el) for el in thing]
    else:
        # thing is either a 0 or 1 length tuple
        if len(thing) == 0:
            return None
        elif len(thing) == 1:
            return thing[0]
        else:
            # shouldn't be norming this thing
            raise IndexError("norming something of length {}"
                             .format(len(thing)))
    return thing

# mark this file as the driver instead of pyaib.dbd.sqlite
# also set by db.backend in the config
@db_driver
class SqliteDriver:
    """SQLite3 database driver"""
    def __init__(self, config):
        path = config.path
        if not path:
            raise RuntimeError("Missing 'path' config for database driver")
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.OperationalError as e:
            # can't open db!
            raise
        print("Database Driver loaded!")
        self._create_database()

    def _check_exists(self, name, type='table'):
        """Check if something exists in the database"""
        c = self.conn.cursor()
        if type == 'channel':
            c.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='messages_{}'
                      """.format(name[1:]))
        else:
            c.execute("""
                SELECT name FROM sqlite_master
                WHERE type='{}' AND name='{}'
                      """.format(type, name))
        return bool(c.fetchone())

    def _create_database(self):
        """Create tables if they don't already exist"""
        if self._check_exists('channels'):
            dbprint("DB already exists")
        else:
            dbprint("Creating database...")
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY,
                channel_name TEXT NOT NULL UNIQUE,
                date_checked TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                autojoin BOOLEAN NOT NULL
                    CHECK (autojoin IN (0,1))
                    DEFAULT 1,
                helen_active BOOLEAN NOT NULL
                    CHECK (helen_active IN (0,1))
                    DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                controller BOOLEAN NOT NULL
                    CHECK (controller IN (0,1))
                    DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS channels_users (
                channel_id INTEGER NOT NULL
                    REFERENCES channels(id),
                user_id INTEGER NOT NULL
                    REFERENCES users(id),
                user_mode CHARACTER(1),
                UNIQUE(channel_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS user_aliases (
                user_id INTEGER NOT NULL
                    REFERENCES users(id),
                alias TEXT NOT NULL,
                type TEXT NOT NULL
                    CHECK (type IN ('irc','wiki','discord')),
                most_recent_irc BOOLEAN NOT NULL
                    CHECK (most_recent_irc IN (0,1))
                    DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                scp_num TEXT,
                parent TEXT,
                ups INTEGER NOT NULL,
                downs INTEGER NOT NULL,
                date_posted TEXT NOT NULL,
                is_promoted BOOLEAN NOT NULL
                    CHECK (is_promoted IN (0,1))
                    DEFAULT 0,
                date_checked TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS articles_tags (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                tag TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS articles_authors (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                author TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS showmore_list (
                channel_id INTEGER NOT NULL
                    REFERENCES channels(id),
                id INTEGER NOT NULL,
                article_id INTEGER NOT NULL
            );""")
        # Will also need a messages table for each channel
        self.conn.commit()

    def issue(self, query):
        """For accepting refactoring (commands/refactor.py)"""
        dbprint("Refactoring database")
        c = self.conn.cursor()
        dbprint("Executing...")
        c.executescript(query)
        dbprint("Committing...")
        self.conn.commit()

    def join_channel(self, channel):
        """Populate a new channel in the database"""
        c = self.conn.cursor()
        # create a new entry in channels
        # will be IGNOREd if channel already exists (UNIQUE constraint)
        c.execute("""
            INSERT OR IGNORE INTO channels
                (channel_name)
            VALUES (?)
                  """, (channel, ))
        # create a new messages_x channel for message logging
        # XXX For messages_channel, # is NOT present XXX
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages_{} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender INTEGER NOT NULL
                    REFERENCES users(id),
                date TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                message TEXT NOT NULL
                 )""".format(channel[1:]))
        self.conn.commit()
        dbprint("Created {}".format(channel))
        # each channel in channels shoud have a messages_channelname
        # might be an idea to make a function that checks

    def get_all_tables(self):
        """Returns a list of all tables"""
        c = self.conn.cursor()
        c.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
                  """)
        # convert list of tuples to list of strings
        return norm(c.fetchall())

    def print_one_table(self, table):
        """Pretty print a single table"""
        try:
            print(pd.read_sql_query("SELECT * FROM {}".format(table),
                                    self.conn))
        except pd.io.sql.DatabaseError:
            # fail silently so that users can't see what channels exist
            print("The table {} does not exist.".format(table))

    def get_all_users(self):
        """Returns a list of all users"""
        # For now, just return aliases
        # TODO return actual users
        c = self.conn.cursor()
        c.execute("""
            SELECT alias FROM user_aliases
                  """)
        return norm(c.fetchall())

    def get_aliases(self, nick):
        """Returns all of someone's aliases"""
        c = self.conn.cursor()
        c.execute("""
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  """, (nick, ))
        ids = norm(c.fetchall())
        if len(ids) == 0:
            return None
        else:
            result = []
            # list of lists
            for id in ids:
                c.execute("""
                    SELECT alias FROM user_aliases
                    WHERE user_id=?
                          """, (id, ))
                result.append(norm(c.fetchall()))
            return result

    def get_generic_id(self, search):
        """Returns from users, channels, articles"""
        c = self.conn.cursor()
        if search[0] == '#':
            type = 'channel'
            c.execute("""
                SELECT id FROM channels
                WHERE channel_name=?
                      """, (search, ))
            id = norm(c.fetchone())
            if not id:
                return None, type
        else:
            type = 'user'
            c.execute("""
                SELECT user_id FROM user_aliases
                WHERE alias=?
                      """, (search, ))
            id = norm(c.fetchone())
            if not id:
                type = 'article'
                c.execute("""
                    SELECT id FROM articles
                    WHERE url=?
                          """, (search, ))
                id = norm(c.fetchone())
                if not id:
                    return None, type
        return id, type

    def get_occupants(self, channel, convert_to_nicks=False):
        """Get a list of current occupants of a channel."""
        if channel[0] != '#':
            raise ValueError("Channel name must start with #.")
        c = self.conn.cursor()
        # find out the channel id
        c.execute("""
            SELECT id FROM channels WHERE channel_name=?
                  """, (channel, ))
        id = norm(c.fetchone())
        dbprint("get_occupants: id is {}".format(id))
        assert id is not None, "Channel {} does not exist.".format(channel)
        # get the occupants
        c.execute("""
            SELECT user_id FROM channels_users WHERE channel_id=?
                  """, (id, ))
        users = norm(c.fetchall())
        dbprint("get_occupants: users is {}".format(join(",",users)))
        assert len(users) > 0, "There are no users in {}.".format(channel)
        if convert_to_nicks:
            users = [self.get_current_nick(id) for id in users]
        return users

    def get_current_nick(self, id):
        """Gets the current nick of a user."""
        c = self.conn.cursor()
        c.execute("""
            SELECT current_nick FROM users WHERE id=?
                  """, (id, ))
        return norm(c.fetchone())

    def sort_names(self, channel, names):
        """Sort the results of a NAMES query"""
        # should already have channel row + table set up.
        if not self._check_exists(channel, 'channel'):
            dbprint('{} does not exist, creating'.format(channel), True)
            self.join_channel(channel)
        # names is a list of objects {nick, mode}
        # 1. add new users and user_aliases
        for name in names:
            name['id'] = self.add_user(name['nick'])
        # 2. add NAMES to channels_users
        c = self.conn.cursor()
        c.execute("""
            SELECT id FROM channels WHERE channel_name=?
                  """, (channel, ))
        channel = norm(c.fetchone())
        assert isinstance(channel, int)
        # need to delete old NAMES data for this channel
        # (may want to waive this in the future for single user changes)
        c.execute("""
            DELETE FROM channels_users WHERE channel_id=?
                  """, (channel, ))
        # then add new NAMES data
        for name in names:
            c.execute("""
                INSERT OR REPLACE INTO channels_users
                    (channel_id, user_id, user_mode)
                VALUES( ? , ? , ? )
                      """, (channel, name['id'], name['mode']))
        # 3. updates in channels when this channel was last checked
        c.execute("""
            UPDATE channels
            SET date_checked=CURRENT_TIMESTAMP
            WHERE channel_name=?
                  """, (channel, ))
        # 4. TODO what else needs to be done?

    def add_user(self, alias, type='irc'):
        """Adds/updates a user and returns their ID"""
        c = self.conn.cursor()
        c.execute("""
            SELECT user_id FROM user_aliases WHERE alias=? AND type=?
                  """, (alias, type))
        result = c.fetchall()
        if result:
            # this alias already exists
            if len(result) == 1:
                dbprint("User {} already exists as ID {}"
                        .format(nickColor(alias), norm(result)[0]))
                # unambiguous user, yay!
                # result = [(3,)] - we only want the number
                return norm(result)[0]
            else:
                # BIG PROBLEM
                # TODO
                dbprint("USER {} IS AMBIGUOUS".format(alias), True)
                return result
        else:
            # this alias does not already exist
            # 1. create a new user
            c.execute("""
                INSERT INTO users DEFAULT VALUES
                      """)
            new_user_id = c.lastrowid
            dbprint("Adding user {} as ID {}"
                    .format(nickColor(alias), new_user_id))
            # 2. add the alias
            c.execute("""
                INSERT INTO user_aliases (alias, type, user_id)
                VALUES ( ? , ? , ? )
                       """, (alias, type, new_user_id))
            self.conn.commit()
            return new_user_id

    def rename_user(self, old, new, force=False):
        """Adds a new alias for a user"""
        # make sure to handle when a user renames to an alias that exists
        # check if either name already exists (old should)
        c = self.conn.cursor()
        c.execute("""
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  """, (old, ))
        old_result = c.fetchall()
        print("old_result:")
        print(old_result)
        if len(old_result) == 0:
            # the old name does not exist
            old_result = None
        elif len(old_result) == 1:
            old_result = norm(old_result)
        else:
            # there's more than one user with this nick
            # ignore for now?
            pass
        c.execute("""
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  """, (new, ))
        new_result = c.fetchall()
        print("new_result:")
        print(new_result)
        if len(new_result) == 0:
            # the new name does not exist
            new_result = None
        elif len(new_result) == 1:
            new_result = norm(new_result)[0]
        else:
            # there's more than one user with this nick
            # ignore for now?
            pass
        if old_result == new_result:
            if old_result is None:
                # this is a new user who joined after the last names
                self.add_user(old)
                self.rename_user(old, new)
                pass
            else:
                # both already marked as the same user, nothing to do here
                pass
        else:
            if old_result is None:
                # an old user happened to join with a new name
                pass
            elif new_result is None:
                # new is unassociated, but old is
                # merge the new name into the old
                dbprint("Adding a new nick to {}".format(old))
                print(old_result)
                print(new)
                c.execute("""
                    INSERT INTO user_aliases (user_id, alias, type)
                    VALUES ( ? , ? , ? )
                          """, (old_result, new, 'irc'))
                self.conn.commit()
            else:
                # both nicks are associated with different users
                # what the fuck do we do here??
                force = True # fuck it, just steal the nick
                # probably need to work out which nick is regged
                    # we can do that!
                    # save the modes of channels when we NAMES them
                    # if the channel is +R, then each name THAT JOINS must be r
                if force:
                    # force the change
                    dbprint("Stealing {} from {}" .format(new, old))
                    # ^TODO make that more informative (wikiname?)
                    c.execute("""
                        DELETE FROM user_aliases
                        WHERE alias=?
                              """, (new, ))
                    c.execute("""
                        INSERT INTO user_aliases (user_id, alias, type)
                        VALUES ( ? , ? , ? )
                              """, (new_result, new, 'irc'))
                    self.conn.commit()
                else:
                    # prompt the user for confirmation?
                    pass
