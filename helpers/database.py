"""database.py

SQLite3 database driver for TARS.

Plugin responsible for accessing and modifying the database.
ALL database queries MUST pass through this file.
Provides functions for manipulating the database.
"""
# reminder: conn.commit() after making changes (i.e. not queries)
# reminder: 'single quotes' for string literals eg for tables that don't exist

from pyaib.db import db_driver
import sqlite3

def dbprint(text, error=False):
    bit = "[\x1b[38;5;28mdb_driver\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

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
        dbprint("Created a new channel")
        c = self.conn.cursor()
        # create a new entry in channels
        # will be IGNOREd if channel already exists (UNIQUE constraint)
        c.execute("""
            INSERT OR IGNORE INTO channels
                (channel_name)
            VALUES (?)
                  """, (channel))
        # create a new messages_x channel for message logging
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages_{} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender INTEGER NOT NULL
                    REFERENCES users(id),
                date TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                message TEXT NOT NULL
            )""".format(channel))
        self.conn.commit()
        # each channel in channels shoud have a messages_channelname
        # might be an idea to make a function that checks

    def get_all_tables(self):
        """Returns a list of all tables"""
        c = self.conn.cursor()
        c.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
                  """)
        # convert list of tuples to list of strings
        return [''.join(names) for names in c.fetchall()]
