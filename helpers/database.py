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
        self.create_database()

    def create_database(self):
        c = self.conn.cursor()
        c.execute("""
          CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            date_checked TEXT NOT NULL,
            autojoin BOOLEAN NOT NULL CHECK (autojoin IN (0,1)),
            helen_active BOOLEAN NOT NULL CHECK (helen_active IN (0,1))
         );""")
        # users stores wiki, irc and discord users
        c.execute("""
          CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            controller BOOLEAN NOT NULL CHECK (controller IN (0,1)),
            seen TEXT NOT NULL
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS channels_users (
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_mode CHARACTER(1),
            FOREIGN KEY(channel_id) REFERENCES channels(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS user_aliases (
            user_id INTEGER NOT NULL,
            alias TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('irc','wiki','discord')),
            FOREIGN KEY(user_id) REFERENCES users(id)
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            scp_num TEXT,
            parent TEXT,
            is_promoted BOOLEAN NOT NULL CHECK (is_promoted IN (0,1)),
            date_posted TEXT NOT NULL,
            date_checked TEXT NOT NULL,
            ups INTEGER NOT NULL,
            downs INTEGER NOT NULL
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS articles_tags (
            article_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY(article_id) REFERENCES articles(id)
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS articles_authors (
            article_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            FOREIGN KEY(article_id) REFERENCES articles(id)
         );""")
        c.execute("""
          CREATE TABLE IF NOT EXISTS showmore_list (
            channel_id INTEGER NOT NULL,
            id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            FOREIGN KEY(channel_id) REFERENCES channels(id)
         );""")
        # Will also need a messages table for each channel
        self.conn.commit()
