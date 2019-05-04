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

def dbprint(text, error=False):
    bit = "[\x1b[38;5;28mdb_driver\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

def norm(thing):
    """fetchX often returns a tuple or a list of tuples because it's dumb"""
    if thing is None:
        return None
    if all(isinstance(el, list) for el in thing):
        thing = [norm(el) for el in thing]
    else:
        # thing is either a 0 or 1 length tuple
        if len(thing) == 0:
            return None
        elif len(thing) == 1:
            return thing[0]
        else:
            # shouldn't be norming this thing
            raise IndexError
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL,
                date_checked TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                autojoin BOOLEAN NOT NULL
                    CHECK (autojoin IN (0,1))
                    DEFAULT 1,
                helen_active BOOLEAN NOT NULL
                    CHECK (helen_active IN (0,1))
                    DEFAULT 0
            );""")
        # users stores wiki, irc and discord users
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                controller BOOLEAN NOT NULL
                    CHECK (controller IN (0,1))
                    DEFAULT 0
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS channels_users (
                channel_id INTEGER NOT NULL
                    REFERENCES channels(id),
                user_id INTEGER NOT NULL
                    REFERENCES users(id),
                user_mode CHARACTER(1)
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_aliases (
                user_id INTEGER NOT NULL
                    REFERENCES users(id),
                alias TEXT NOT NULL,
                type TEXT NOT NULL
                    CHECK (type IN ('irc','wiki','discord'))
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles_tags (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                tag TEXT NOT NULL
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles_authors (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                author TEXT NOT NULL
            );""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS showmore_list (
                channel_id INTEGER NOT NULL
                    REFERENCES channels(id),
                id INTEGER NOT NULL,
                article_id INTEGER NOT NULL
            );""")
        # Will also need a messages table for each channel
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

    def get_all_users(self):
        """Returns a list of all users"""
        # For now, just return aliases
        # TODO return actual users
        c = self.conn.cursor()
        c.execute("""
            SELECT alias FROM user_aliases
                  """)
        return norm(c.fetchall())

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

    def sort_names(self, channel, names):
        """Sort the results of a NAMES query"""
        # should already have channel row + table set up.
        if not self._check_exists(channel, 'channel'):
            dbprint('{} does not exist, creating'.format(channel), True)
            self.join_channel(channel)
        # names is a list of objects {name, mode}
        just_names = [user['nick'] for user in names]
        # 1. add new users and user_aliases
        for name in just_names:
            self.add_user(name)
        # 2. add NAMES to channels_users
        c = self.conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO
                  """)
        # 3. updates in channels when this channel was last checked
        # 4. 

    def add_user(self, alias, type='irc'):
        """Adds/updates a user and returns their ID"""
        c = self.conn.cursor()
        c.execute("""
            SELECT user_id FROM user_aliases WHERE alias=? AND type=?
                  """, (alias, type))
        result = c.fetchall()
        dbprint("Adding user {}".format(alias))
        pprint(result)
        if result:
            # this alias already exists
            if len(result) == 1:
                # unambiguous user, yay!
                return result[0]
            else:
                # BIG PROBLEM
                # TODO
                return result
        else:
            # this alias does not already exist
            # 1. create a new user
            c.execute("""
                INSERT INTO users DEFAULT VALUES
                      """)
            # 2. add the alias
            c.execute("""
                INSERT INTO user_aliases (alias, type, user_id)
                VALUES ( ? , ? , ? )
                       """, (alias, type, c.lastrowid))
            self.conn.commit()

    def rename_user(self, old, new):
        """Adds a new alias for a user"""
        # make sure to handle when a user renames to an alias that already
        # exists
