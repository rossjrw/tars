"""database.py

SQLite3 database driver for TARS.

Plugin responsible for accessing and modifying the database.
ALL database queries MUST pass through this file.
Provides functions for manipulating the database.
"""
# reminder: conn.commit() after making changes (i.e. not queries)
# reminder: 'single quotes' for string literals eg for tables that don't exist

import sqlite3
import random
import pandas
import pendulum as pd
from pypika import MySQLQuery, Table, Order
from pypika.terms import ValueWrapper
from pypika.functions import Max, Length
from pyaib.irc import Message
from helpers.config import CONFIG
from helpers.error import nonelist
try:
    import re2 as re
except ImportError:
    print("re2 failed to load, falling back to re")
    import re

DB = {} # is instantiated as SqliteDriver at the end of this file

sqlite3.enable_callback_tracebacks(True)

def dbprint(text, error=False):
    bit = "[\x1b[38;5;108mDatabase\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

def norm(thing):
    """fetchX often returns a tuple or a list of tuples because it's dumb"""
    # This function needs to fucking go
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
            if isinstance(thing[0], sqlite3.Row):
                return thing
            # shouldn't be norming this thing
            raise IndexError("norming something of length {}"
                             .format(len(thing)))
    return thing

def _regexp(expr, item):
    """For evaluating db strings against a given regex."""
    if item is None: return False
    return re.search(expr, item, re.IGNORECASE) is not None

def _glob(expr, item):
    """For evaluating db strings against a given string."""
    if item is None: return False
    return expr.lower() in item.lower()

# mark this file as the driver instead of pyaib.dbd.sqlite
# also set by db.backend in the config
class SqliteDriver:
    """SQLite3 database driver"""
    def __init__(self):
        path = CONFIG['db']['driver.database']['path']
        if not path:
            raise RuntimeError("Missing 'path' config for database driver")
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.OperationalError as e:
            dbprint("The database could not be opened", True)
            raise
        self._create_database()
        self.conn.row_factory = sqlite3.Row
        self.conn.create_function("REGEXP", 2, _regexp)
        self.conn.create_function("GLOB", 2, _glob)
        self.set_controller(CONFIG.owner)

    def commit(self):
        """Just commits the database.
        For use by external functions after batch operations.
        To be used in conjuction with optional committing."""
        self.conn.commit()

    def _check_exists(self, name, type='table'):
        """Check if something exists in the database"""
        c = self.conn.cursor()
        if type == 'channel':
            c.execute('''
                SELECT channel_name FROM channels
                WHERE channel_name=?
                      ''', (name, ))
        elif type == 'alias':
            c.execute('''
                SELECT alias FROM user_aliases
                WHERE alias=?
                      ''', (name, ))
        elif type == 'user':
            raise AttributeError("Seems weird to check for user, not alias")
        elif type == 'table':
            c.execute('''
                SELECT name FROM sqlite_master
                WHERE type=? AND name=?
                      ''', (type, name))
        else:
            raise AttributeError("Checking existence of {} of unknown type {}"
                                 .format(name, type))
        return bool(c.fetchone())

    def _create_database(self):
        """Create tables if they don't already exist"""
        if self._check_exists('channels'):
            dbprint("DB already exists")
        else:
            dbprint("Creating database...")
        c = self.conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY,
                channel_name TEXT NOT NULL
                    COLLATE NOCASE,
                date_checked TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                autojoin BOOLEAN NOT NULL
                    CHECK (autojoin IN (0,1))
                    DEFAULT 1,
                helen_active BOOLEAN NOT NULL
                    CHECK (helen_active IN (0,1))
                    DEFAULT 0,
                UNIQUE (channel_name COLLATE NOCASE)
            );
            INSERT OR REPLACE INTO channels (id, channel_name, autojoin)
                VALUES (
                    (SELECT id FROM channels WHERE channel_name='private'),
                    'private',
                    0
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
                alias TEXT NOT NULL
                    COLLATE NOCASE,
                type TEXT NOT NULL
                    CHECK (type IN ('irc','wiki','discord')),
                most_recent BOOLEAN NOT NULL
                    CHECK (most_recent IN (0,1))
                    DEFAULT 0,
                weight BOOLEAN NOT NULL
                    CHECK (weight IN (0,1))
                    DEFAULT 0,
                UNIQUE(user_id, alias, type, weight)
            );
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL
                    COLLATE NOCASE,
                category TEXT NOT NULL
                    DEFAULT '_default',
                title TEXT,
                scp_num TEXT,
                parent TEXT,
                rating INTEGER NOT NULL,
                ups INTEGER,
                downs INTEGER,
                date_posted INTEGER NOT NULL,
                is_promoted BOOLEAN NOT NULL
                    CHECK (is_promoted IN (0,1))
                    DEFAULT 0,
                date_checked INTEGER NOT NULL
                    DEFAULT (CAST(STRFTIME('%s','now') AS INT)),
                UNIQUE(url)
            );
            CREATE TABLE IF NOT EXISTS articles_tags (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                tag TEXT NOT NULL
                    COLLATE NOCASE,
                UNIQUE(article_id, tag)
            );
            CREATE TABLE IF NOT EXISTS articles_authors (
                article_id INTEGER NOT NULL
                    REFERENCES articles(id),
                author TEXT NOT NULL
                    COLLATE NOCASE,
                metadata BOOLEAN NOT NULL
                    CHECK (metadata IN (0,1))
                    DEFAULT 0,
                UNIQUE(article_id, author, metadata)
            );
            CREATE TABLE IF NOT EXISTS showmore_list (
                channel_id INTEGER NOT NULL
                    REFERENCES channels(id),
                id INTEGER NOT NULL,
                article_id INTEGER NOT NULL,
                UNIQUE(channel_id, id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                channel_id INTEGER
                    REFERENCES channels(id),
                kind TEXT NOT NULL
                    DEFAULT 'PRIVMSG',
                sender TEXT NOT NULL
                    COLLATE NOCASE,
                command BOOLEAN NOT NULL
                    CHECK (command IN (0,1))
                    DEFAULT 0,
                timestamp INTEGER NOT NULL,
                message TEXT NOT NULL,
                ignore BOOLEAN NOT NULL
                    CHECK (ignore IN (0,1))
                    DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS gibs (
                id INTEGER PRIMARY KEY,
                message TEXT NOT NULL,
                UNIQUE(message)
            )''')
        # Will also need a messages table for each channel
        self.conn.commit()

    def issue(self, query, callback=None, **kwargs):
        """For accepting refactoring (commands/refactor.py)
        Pass commit=False for no commit"""
        dbprint("Refactoring database")
        c = self.conn.cursor()
        dbprint("Executing...")
        c.execute(query)
        dbprint("Committing...")
        ret = ""
        if query.startswith("SELECT"):
            pattern = r"^SELECT\s(\S+)"
            keys = re.match(pattern, query).group(1).split(',')
            results = c.fetchall()
            for result in results:
                for key in keys:
                    print(result[key])
                    ret += str(result[key]) + " "
        elif kwargs.get('commit', True):
            self.conn.commit()
        if callback is not None:
            callback(ret)
        else:
            return ret

    def join_channel(self, channel):
        """Populate a new channel in the database"""
        c = self.conn.cursor()
        # create a new entry in channels
        # will be IGNOREd if channel already exists (UNIQUE constraint)
        c.execute('''
            INSERT OR IGNORE INTO channels
                (channel_name)
            VALUES (?)
                  ''', (channel, ))
        c.execute('''
            UPDATE channels
            SET autojoin=1
            WHERE channel_name=?
                  ''', (channel,))
        self.conn.commit()
        dbprint("Joined {}".format(channel))

    def leave_channel(self, channel):
        """Leave a channel"""
        c = self.conn.cursor()
        c.execute('''
            UPDATE channels
            SET autojoin=0
            WHERE channel_name=?
                  ''', (channel,))
        self.conn.commit()
        dbprint("Left {}".format(channel))

    def get_autojoins(self):
        """Get all channels that the bot was in last time"""
        c = self.conn.cursor()
        c.execute('''
            SELECT channel_name FROM channels
            WHERE autojoin=1
                  ''')
        return [r['channel_name'] for r in c.fetchall()]

    def get_all_tables(self):
        """Returns a list of all tables"""
        c = self.conn.cursor()
        c.execute('''
            SELECT name FROM sqlite_master WHERE type='table'
                  ''')
        # convert list of tuples to list of strings
        return [row['name'] for row in c.fetchall()]

    def print_one_table(self, table):
        """Pretty print a single table"""
        try:
            df = pandas.read_sql_query("SELECT * FROM {}".format(table),self.conn)
            if table == 'user_aliases':
                df.sort_values('user_id', inplace=True)
            print(df)
        except pandas.io.sql.DatabaseError:
            # fail silently so that users can't see what channels exist
            print("The table {} does not exist.".format(table))

    def print_selection(self, query):
        """Pretty print a selection"""
        try:
            df = pandas.read_sql_query(query, self.conn)
            print(df)
        except pandas.io.sql.DatabaseError as e:
            # fail silently
            dbprint("There was a problem with the selection statement.", True)
            raise

    def get_all_users(self):
        """Returns a list of all users"""
        # For now, just return aliases
        # TODO return actual users
        c = self.conn.cursor()
        c.execute('''
            SELECT alias FROM user_aliases
                  ''')
        return [r['alias'] for r in c.fetchall()]

    def get_messages(self, channels, users=None, senders=None, patterns=None,
                     contains=None, minlength=None, limit=None):
        """Returns all messages from the channel by the user.\
        user, sender, pattern, contains should be lists (and channel can be)."""
        c = self.conn.cursor()
        print("Getting messages")
        # TODO make this lookup all names of a user and do an IN check
        # need to convert channel name to channel id
        if not isinstance(channels, list): channels = [channels]
        for channel in channels:
            assert isinstance(channel, str) and channel.startswith('#')
        assert isinstance(users, (list, type(None)))
        assert isinstance(senders, (list, type(None)))
        assert isinstance(patterns, (list, type(None)))
        assert isinstance(contains, (list, type(None)))
        assert isinstance(minlength, (int, type(None)))
        assert isinstance(limit, (int, type(None)))
        c.execute('''
            SELECT id FROM channels
            WHERE channel_name IN ({})'''.format(",".join(["?"]*len(channels)))
                  , channels)
        channels = [row['id'] for row in c.fetchall()]
        if None in channels:
            raise ValueError("That channel does not exist")
        messages = Table('messages')
        q = MySQLQuery.from_(messages).select(messages.message)
        q = q.where(messages.channel_id.isin(channels))
        q = q.where(messages.command == 0)
        q = q.where(messages.kind == 'PRIVMSG')
        q = q.where(messages.ignore == 0)
        # if user is not None: TODO
        #     q = q.where(messages.sender == user)
        if not nonelist(senders):
            senders_in = [s.lstrip("+") for s in senders
                          if not s.startswith("-")]
            senders_out = [s.lstrip("-") for s in senders
                           if s.startswith("-")]
            if len(senders_in):
                q = q.where(messages.sender.isin(senders_in))
            if len(senders_out):
                q = q.where(messages.sender.notin(senders_out))
        if not nonelist(patterns):
            for pattern in patterns:
                q = q.where(messages.message.regex(pattern))
        if not nonelist(contains):
            for contain in contains:
                q = q.where(messages.message.like(contain))
        if minlength is not None:
            q = q.where(Length(messages.message) >= minlength)
        q = q.orderby(messages.timestamp, order=Order.desc)
        if limit is not None:
            q = q[:limit]
        q = str(q).replace(" LIKE "," GLOB ").replace(" REGEX "," REGEXP ")
        print("Getting messages:", str(q))
        c.execute(str(q))
        result = c.fetchall()
        messages = [m['message'] for m in result]
        return messages

    def get_most_recent_message(self, channel):
        """Get the ID of the most recent message in a channel."""
        assert channel.startswith('#')
        c = self.conn.cursor()
        c.execute('''
            SELECT MAX(id) FROM messages
            WHERE channel_id=(SELECT id FROM channels
                              WHERE channel_name=?)
            AND kind='PRIVMSG'
                  ''', (channel,))
        return int(c.fetchone()['MAX(id)'])

    def get_messages_between(self, channel, start, end):
        """Get all messages between 2 ids in a channel, inclusive."""
        assert channel.startswith('#')
        c = self.conn.cursor()
        c.execute('''
            SELECT * FROM messages
            WHERE id BETWEEN ? AND ?
            AND (kind='NICK' OR kind='QUIT'
                 OR channel_id=(SELECT id FROM channels
                                WHERE channel_name=?))
                  ''', (start, end, channel))
        rows = c.fetchall()
        return rows

    def get_messages_to_command_limit(self, channel, limit):
        """Get all messages from most recent up to the specified number of
        commands"""
        assert channel.startswith('#')
        c = self.conn.cursor()
        c.execute('''
            SELECT message FROM messages
            WHERE id >= (SELECT min(id) FROM (
                  SELECT id FROM messages
                  WHERE command=1
                  AND channel_id=(SELECT id FROM channels
                                  WHERE channel_name=?)
                  AND kind='PRIVMSG'
                  ORDER BY id DESC
                  LIMIT ?))
            AND channel_id=(SELECT id FROM channels
                            WHERE channel_name=?)
            AND kind='PRIVMSG'
                  ''', (channel, limit, channel))
        return [m['message'] for m in c.fetchall()]

    def add_gib(self, gib):
        """Add a gib"""
        c = self.conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO gibs( message )
            VALUES( ? )
                  ''', (gib,))
        self.conn.commit()

    def get_gibs(self):
        """Return all previous gibs"""
        c = self.conn.cursor()
        c.execute('''
            SELECT message FROM gibs
                  ''')
        return [row['message'] for row in c.fetchall()]

    def get_aliases(self, nick):
        """Returns all of someone's aliases
        nick can be an alias or an ID"""
        c = self.conn.cursor()
        if nick is None:
            c.execute('''
                SELECT alias FROM user_aliases
                      ''')
            return [row['alias'] for row in c.fetchall()]
        if isinstance(nick, int):
            ids = [nick]
        else:
            c.execute('''
                SELECT user_id FROM user_aliases
                WHERE alias=?
                    ''', (nick, ))
            ids = c.fetchall()
        if len(ids) == 0:
            return None
        else:
            result = []
            # list of lists
            for id in ids:
                c.execute('''
                    SELECT alias FROM user_aliases
                    WHERE user_id=?
                          ''', (id, ))
                result.extend(c.fetchall())
            return [row['alias'] for row in result]

    def get_channel_members(self, channel):
        """Returns a list of all user possible nicks currently in a channel
        Not limited to actual channel nick list - see get_occupants"""
        # TODO exhaustive most_recent checking
        c = self.conn.cursor()
        # get all ids in channel
        c.execute('''
            SELECT user_id FROM channels_users
            WHERE channel_id=(
                SELECT id FROM channels
                WHERE channel_name=?)
                  ''', (channel,))
        ids = [row['user_id'] for row in c.fetchall()]
        # then get the aliases of those ids
        c.execute('''
            SELECT alias FROM user_aliases
            WHERE user_id IN ({})'''.format(','.join(['?']*len(ids)))
                  , [str(id) for id in ids])
        return [row['alias'] for row in c.fetchall()]

    def get_generic_id(self, search):
        """Returns from users, channels, articles"""
        c = self.conn.cursor()
        if search[0] == '#':
            type = 'channel'
            c.execute('''
                SELECT id FROM channels
                WHERE channel_name=?
                      ''', (search, ))
            id = norm(c.fetchone())
            if not id:
                return None, type
        else:
            type = 'user'
            c.execute('''
                SELECT user_id FROM user_aliases
                WHERE alias=?
                      ''', (search, ))
            id = norm(c.fetchone())
            if not id:
                type = 'article'
                c.execute('''
                    SELECT id FROM articles
                    WHERE url=?
                          ''', (search, ))
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
        c.execute('''
            SELECT id FROM channels WHERE channel_name=?
                  ''', (channel, ))
        id = norm(c.fetchone())
        assert id is not None, "Channel {} does not exist.".format(channel)
        # get the occupants
        c.execute('''
            SELECT user_id FROM channels_users WHERE channel_id=?
                  ''', (id, ))
        users = c.fetchall()
        dbprint("get_occupants: users is {}".format(",".join(map(str,users))))
        assert len(users) > 0, "There are no users in {}.".format(channel)
        if convert_to_nicks:
            users = [user['user_id'] for user in users]
            users = [self.get_current_nick(id) for id in users]
        else:
            users = [user['user_id'] for user in users]
        return users

    def get_current_nick(self, id):
        """Gets the current nick of a user."""
        c = self.conn.cursor()
        c.execute('''
            SELECT alias FROM user_aliases
            WHERE most_recent=1 AND user_id=? AND type='irc'
                  ''', (id, ))
        name = norm(c.fetchone())
        if name:
            return name
        else:
            c.execute('''
                SELECT alias FROM user_aliases
                WHERE user_id=?
                      ''', (id, ))
            name = random.choice(norm(c.fechall()))
            return "??{}".format(name)

    def get_all_channels(self):
        c = self.conn.cursor()
        c.execute('''
            SELECT channel_name FROM channels
            WHERE NOT channel_name='private'
                  ''')
        return [row['channel_name'] for row in c.fetchall()]

    def get_controllers(self):
        """Gets bot controllers"""
        c = self.conn.cursor()
        c.execute('''
            SELECT alias FROM user_aliases
            WHERE user_id IN (SELECT id FROM users
                              WHERE controller=1)
                  ''')
        return [row['alias'] for row in c.fetchall()]

    def set_controller(self, user):
        if isinstance(user, str):
            id = self.get_user_id(user)
        else:
            id = user
        c = self.conn.cursor()
        c.execute('''
            UPDATE users SET controller=1 WHERE id=?
                  ''', (id,))
        self.conn.commit()
        print("Added {} as controller".format(user))


    def get_user_id(self, alias):
        """Get the user id from the alias"""
        c = self.conn.cursor()
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  ''', (alias,))
        ids = [row['user_id'] for row in c.fetchall()]
        if len(ids) == 0:
            return None
        elif len(ids) == 1:
            return ids[0]
        else:
            raise Exception("More than one ID for alias {}".format(alias))

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
        c.execute('''
            SELECT id FROM channels WHERE channel_name=?
                  ''', (channel, ))
        channel = norm(c.fetchone())
        assert isinstance(channel, int)
        # need to delete old NAMES data for this channel
        # (may want to waive this in the future for single user changes)
        c.execute('''
            DELETE FROM channels_users WHERE channel_id=?
                  ''', (channel, ))
        # then add new NAMES data
        for name in names:
            c.execute('''
                INSERT OR REPLACE INTO channels_users
                    (channel_id, user_id, user_mode)
                VALUES( ? , ? , ? )
                      ''', (channel, name['id'], name['mode']))
        # 3. updates in channels when this channel was last checked
        c.execute('''
            UPDATE channels
            SET date_checked=CURRENT_TIMESTAMP
            WHERE id=?
                  ''', (channel, ))
        # 4. TODO what else needs to be done?
        self.conn.commit()

    def get_last_sort(self, channel):
        """Get the time at which the channel's names were last sorted"""
        c = self.conn.cursor()
        c.execute('''
            SELECT date_checked FROM channels
            WHERE channel=?
                  ''', (channel,))
        return c.fetchone()['date_checked']

    def add_user(self, alias, type='irc'):
        """Adds/updates a user and returns their ID"""
        c = self.conn.cursor()
        c.execute('''
            SELECT user_id FROM user_aliases WHERE alias=? AND type=?
                  ''', (alias, type))
        result = c.fetchall()
        if result:
            # this alias already exists
            # c.execute('''
            #     UPDATE user_aliases SET most_recent=0
            #     WHERE alias=? AND type='irc'
            #           ''', (
            if len(result) == 1:
                # dbprint("User {} already exists as ID {}"
                #         .format(nickColor(alias), norm(result)[0]))
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
            c.execute('''
                INSERT INTO users DEFAULT VALUES
                      ''')
            new_user_id = c.lastrowid
            # dbprint("Adding user {} as ID {}"
            #         .format(nickColor(alias), new_user_id))
            # 2. add the alias
            # 2.1 mark the previous alias as not current
            c.execute('''
                INSERT INTO user_aliases (alias, type, user_id)
                VALUES ( ? , ? , ? )
                       ''', (alias, type, new_user_id))
            self.conn.commit()
            return new_user_id

    def add_alias(self, user, alias, weight=0, nick_type='irc'):
        """Adds or updates an alias to a user
        Returns bool if the user/alias combo already existed."""
        # if weight=0 then /nick, if =1 then .alias
        # if weight=0 we can assume that most_recent=True
        assert isinstance(user, int)
        c = self.conn.cursor()
        # first first, let's see if the combo already exists
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE user_id=? AND alias=? AND weight=?
                  ''', (user, alias, weight))
        combo_exists = bool(c.lastrowid)
        print("Combo exists: {}".format(combo_exists))
        # things to do:
            # 1. detect if the user-alias combo already exists
            # if it does, mark as most recento
            # BUT only do this if weight=0
        if weight == 0:
            c.execute('''
                UPDATE user_aliases SET most_recent=0
                WHERE user_id=? AND type=? AND weight=0
                      ''', (user, nick_type))
        c.execute('''
            INSERT OR REPLACE INTO user_aliases
                  (user_id, alias, type, weight, most_recent)
            VALUES ( ? , ? , ? , ? , ? )
                  ''', (user, alias, nick_type, weight,
                        (not weight if nick_type is 'irc' else 0)))
        self.conn.commit()
        return combo_exists

    def remove_alias(self, user, alias, weight=None, nick_type='irc'):
        """Removes an alias from a user
        Returns bool if the user/alias combo already existed."""
        # this function doesn't care about weight?
        assert isinstance(user, int)
        c = self.conn.cursor()
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE user_id=? AND alias=?
                  ''', (user, alias))
        combo_exists = bool(c.lastrowid)
        # things to do:
            # scrap the alias
        c.execute('''
            DELETE FROM user_aliases WHERE user_id=? AND alias=?
                  ''', (user, alias))
        self.conn.commit()
        return combo_exists

    def __rename_user(self, old, new, force=False):
        """Adds a new alias for a user"""
        # when a user renames, add the new nick at weight 0
        # make sure to handle when a user renames to an alias that exists
        # check if either name already exists (old should)
        c = self.conn.cursor()
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  ''', (old, ))
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
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  ''', (new, ))
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
                c.execute('''
                    INSERT INTO user_aliases (user_id, alias, type)
                    VALUES ( ? , ? , ? )
                          ''', (old_result, new, 'irc'))
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
                    c.execute('''
                        DELETE FROM user_aliases
                        WHERE alias=?
                              ''', (new, ))
                    c.execute('''
                        INSERT INTO user_aliases (user_id, alias, type)
                        VALUES ( ? , ? , ? )
                              ''', (new_result, new, 'irc'))
                    self.conn.commit()
                else:
                    # prompt the user for confirmation?
                    pass

    def rename_user(self, old_nick, new_nick):
        """Handle a user changing their name.
        This process operates at weight 0."""
        dbprint("Renaming {} to {}".format(old_nick, new_nick))
        # 1. add the new nick to the current user
        # 2. mark the new nick as active and the old as inactive
        # first: get the current user's ID
        # use the highest available weight for this nick (reduce ambiguity)
        c = self.conn.cursor()
        c.execute('''
            SELECT user_id,weight FROM user_aliases
            WHERE alias=? AND weight=(
                SELECT MAX(weight) FROM user_aliases
                WHERE alias=?
            )
                  ''', (old_nick, old_nick))
        old_id = c.fetchall()
        # old_id should be a single row (multiple if the nick is ambiguous)
        if len(old_id) == 0:
            # the old nick doesn't exist - shouldn't be possible, but fine
            old_id = self.add_user(old_nick)
        elif len(old_id) == 1:
            # expected result
            old_id = old_id[0]['user_id']
        else:
            # the old nick is associated with 2 users
            # set ID to none, try to determine from identity of new nick
            old_id = None
            dbprint("Nick {} is ambiguous".format(old_nick), True)
            # maybe perform the query here?
        # now get the id of the new nick
        c.execute('''
            SELECT user_id,weight FROM user_aliases
            WHERE alias=? AND weight=(
                SELECT MAX(weight) FROM user_aliases
                WHERE alias=?
            )
                  ''', (new_nick, new_nick))
        new_id = c.fetchall()
        if len(new_id) == 0:
            # this is a totally new nick - assign it to the current user
            dbprint("Adding {} to user {}".format(new_nick, old_id))
            self.add_alias(old_id, new_nick)
        elif len(new_id) == 1:
            # this nick is already in use and assigned to a user
            # is it the same user as the current one?
            new_id = new_id[0]['user_id']
            if new_id == old_id:
                # they are the same user! no need to do anything
                dbprint("{} and {} are the same user".format(old_nick, new_nick))
                # TODO mark as most recent
                pass
            else:
                # they are not the same user!
                # use weight to determine ambiguity
                self.add_alias(new_id, old_nick)
                dbprint("Adding {} to user {}".format(old_nick, new_id))
                if old_id is None:
                    self.add_alias(old_id, new_nick)
                    dbprint("Adding {} to user {}".format(new_nick, old_id))
                # that makes no sense but we're running with it
        else:
            # the new nick is ambiguous
            if old_id is None:
                dbprint("Both nick are ambiguous!", True)
                pass
            else:
                pass

    def log_message(self, msg):
        """Logs a message in the db.
        inp should be either a message object or equivalent dict"""
        if isinstance(msg, Message):
            msg = {'channel': msg.channel,
                   'sender': msg.sender,
                   'kind': msg.kind,
                   'message': msg.message,
                   'nick': msg.nick,
                   'args': msg.args,
                   'timestamp': msg.timestamp}
        # Takes PRIVMSG, JOIN, PART, NICK
        chname = "private" if msg['channel'] is None else msg['channel']
        if msg['kind'] == 'NICK': chname = None
        assert msg['kind'] in ['PRIVMSG','JOIN','PART','NICK','QUIT'], msg['kind']
        if msg['kind'] == 'PRIVMSG':
            msgiscmd = msg['message'].startswith((".","!","?","^"))
        else:
            msgiscmd = False
        c = self.conn.cursor()
        # log this message into the messages table
        if chname is not None:
            c.execute('''
                SELECT id FROM channels
                WHERE channel_name=?
                      ''', (chname, ))
            channel = norm(c.fetchone())
            assert isinstance(channel, int), "chname {} id {}".format(chname,channel)
        c.execute('''
            INSERT INTO messages
                (channel_id, kind, sender, timestamp, message, command)
            VALUES ( ? , ? , ? , ? , ? , ? )
                  ''', (channel if msg['kind'] != 'NICK' else None,
                        msg['kind'],
                        msg['nick'],
                        round(msg['timestamp']),
                        (msg['message'] if msg['kind'] == 'PRIVMSG'
                         else msg['args'] if msg['kind'] == 'NICK'
                         else ""),
                        msgiscmd))
        # mark current nick as most recent
        c.execute('''
            SELECT user_id FROM user_aliases
            WHERE alias=?
                  ''', (msg['nick'], ))
        user = c.fetchall()
        if len(user) == 0:
            user = self.add_user(msg['nick'])
        elif len(user) > 1:
            raise ValueError("User {} exists more than once".format(msg['nick']))
        else:
            user = user[0]['user_id']
        assert isinstance(user, int)
        c.execute('''
            UPDATE user_aliases
            SET most_recent=0
            WHERE type='irc' AND user_id=?
                  ''', (user, ))
        c.execute('''
            UPDATE user_aliases
            SET most_recent=1
            WHERE type='irc' AND user_id=? AND alias=?
                  ''', (user, msg['nick']))
        self.conn.commit()

    def add_article(self, article, commit=True):
        """Adds an article and its data to the db.
        article should be a dict as the response from API.get_meta.
        Set commit=False for mass addition, then commit afterwards."""
        # 1. add to articles
        # 1.1. make a new entry if it's a new article
        # 1.2. update the existing entry if the article already exists
        # 2. add to articles_tags
        # 3. add to articles_authors
        # 3.1 [allow metadata to overwrite articles_authors]
        dbprint("Adding article {}".format(article['fullname']))
        c = self.conn.cursor()
        if 'ups' not in article:
            article['ups'] = None
            article['downs'] = None
        else:
            assert 'downs' in article
        if 'fullname' in article:
            if ':' in article['fullname']:
                article['category'] = article['fullname'].split(':')[0]
                article['url'] = article['fullname'].split(':')[1]
            else:
                article['category'] = '_default'
                article['url'] = article['fullname']
        if 'created_by' not in article or article['created_by'] is None:
            article['created_by'] = "an anonymous user"
        # this dict will be fed into the database
        article_data = {
            'url': article['url'],
            'category': article['category'],
            'title': article['title'],
            'scp_num': None,
            'parent': article['parent_fullname'],
            'rating': article['rating'],
            'ups': article['ups'],
            'downs': article['downs'],
            'date_posted': pd.parse(article['created_at']).int_timestamp}
        c.execute('''
            SELECT id FROM articles WHERE url=?
                  ''', (article['url'], ))
        article_data['id'] = norm(c.fetchone())
        if article_data['id'] is None:
            # the article does not already exist
            # replace shouldn't actually happen but hey can't hurt
            c.execute('''
                INSERT OR REPLACE INTO articles
                    (url, category, title, scp_num, parent,
                     rating, ups, downs, date_posted)
                VALUES (:url, :category, :title, :scp_num, :parent,
                        :rating, :ups, :downs, :date_posted)
                      ''', article_data)
            article_data['id'] = c.lastrowid
        else:
            # the article already exists and must be updated
            dbprint("This article already exists", True)
            # ignore ups/downs
            c.execute('''
                UPDATE articles
                SET url=:url, category=:category, title=:title,
                    scp_num=:scp_num, parent=:parent, rating=:rating,
                    date_posted=:date_posted
                WHERE id=:id
                      ''', article_data)
        # update tags and authors
        c.execute('''
            DELETE FROM articles_tags WHERE article_id=?
                  ''', (article_data['id'],))
        c.executemany('''
            INSERT INTO articles_tags (article_id, tag)
            VALUES ( ? , ? )
                      ''', [(article_data['id'],t) for t in article['tags']])
        c.execute('''
            DELETE FROM articles_authors
            WHERE article_id=? AND metadata=0
                  ''', (article_data['id'],))
        c.execute('''
            INSERT INTO articles_authors (article_id, author)
            VALUES ( ? , ? )
                  ''', (article_data['id'], article['created_by']))
        if commit:
            self.conn.commit()

    def add_article_title(self, url, num, title, commit=True):
        """Update the meta title for an SCP"""
        c = self.conn.cursor()
        # for most articles: title is full, scp-num is null
        # for scps: scp-num is fill, title is to be filled
        # possibly TODO throw if scp doesn't exist
        # title is allowed to be None
        c.execute('''
            UPDATE articles
            SET title=?, scp_num=?
            WHERE url=?
                  ''', (title, num, url))
        if commit:
            self.conn.commit()

    def set_authors(self, url, authors, commit=True):
        """Set the authors for a given article."""
        c = self.conn.cursor()
        c.execute('''
            SELECT id FROM articles WHERE url=?
                  ''', (url,))
        page_id = c.fetchone()
        if page_id is None:
            raise ValueError("page {} doesn't exist".format(url))
        page_id = page_id['id']
        c.execute('''
            DELETE FROM articles_authors
            WHERE article_id=?
                  ''', (page_id,))
        c.executemany('''
            INSERT INTO articles_authors (article_id, author)
            VALUES ( ? , ? )
                      ''' , ((page_id, author) for author in authors))
        if commit:
            self.conn.commit()


    def get_article_info(self, id):
        """Gets info about an article"""
        page = {'id': id, 'tags': [], 'authors': []}
        c = self.conn.cursor()
        c.execute('''
            SELECT category,url,title,scp_num,rating,date_posted
            FROM articles WHERE id=?
                  ''', (id,))
        result = c.fetchone()
        for column in result.keys():
            page[column] = result[column]
        # generate the fullname from category:url
        if page['category'] == '_default':
            page['fullname'] = page['url']
        else:
            page['fullname'] = ":".join([page['category'], page['url']])
        # now get authors and tags
        c.execute('''
            SELECT tag FROM articles_tags WHERE article_id=?
                  ''', (id,))
        for row in c.fetchall():
            page['tags'].append(row['tag'])
        # TODO this does not take metadata into account
        c.execute('''
            SELECT author FROM articles_authors WHERE article_id=?
                  ''', (id,))
        for row in c.fetchall():
            page['authors'].append(row['author'])
        return page

    def get_articles(self, searches, selection=None):
        """Get a list of articles that match the criteria.
        searches must be a LIST consisting of DICTS.
        Each dict must contain the following:
            * 'term' - the search term as a string, MinMax or inc/exc list.
            * 'type' - the type of search:
                * None, regex, tags, author, rating, date, category, parent,
                  url
        selection must be a DICT containing the following:
            * 'ignorepromoted' - defaults to False
            * 'order' - the order of the output list:
                * None, random, recommend, recent
            * 'limit' - a limit on the list returned
            * 'offset' - how many articles to offset
        Returns a list of articles. Use get_article_info for more detail on
        each."""
        # loop through searches and query the database, I guess
        # start with the least intensive process, to most intensive:
        keyorder = {'url': 0, 'rating': 0, 'parent': 1, 'category': 2,
                    'date': 3, 'author': 4, 'tags': 5, None: 6, 'regex': 7}
        searches.sort(key=lambda x: keyorder[x['type']])
        # begin query
        art = Table('articles')
        art_au = Table('articles_authors')
        art_tags = Table('articles_tags')
        q = MySQLQuery.from_(art).select(art.id)
        for search in searches:
            if search['type'] == 'rating':
                if search['term']['max'] is not None:
                    q = q.where(art.rating <= search['term']['max'])
                if search['term']['min'] is not None:
                    q = q.where(art.rating >= search['term']['min'])
            elif search['type'] == 'parent':
                q = q.where(art.parent == search['term'])
            elif search['type'] == 'category':
                if len(search['term']['exclude']) > 0:
                    q = q.where(art.category.notin(search['term']['exclude']))
                if len(search['term']['include']) > 0:
                    q = q.where(art.category.isin(search['term']['include']))
            elif search['type'] == 'date':
                if search['term']['max'] is not None:
                    timestamp = search['term']['max'].int_timestamp
                    q = q.where(art.date_posted <= timestamp)
                if search['term']['min'] is not None:
                    timestamp = search['term']['min'].int_timestamp
                    q = q.where(art.date_posted >= timestamp)
            elif search['type'] == 'author':
                # yay for triple-nested queries!
                meta_q = MySQLQuery.from_(art_au).select(Max(art_au.metadata)) \
                         .where(art_au.article_id == art.id)
                au_q = MySQLQuery.from_(art_au).select(art_au.author) \
                       .where(art_au.article_id == art.id) \
                       .where(art_au.metadata == meta_q)
                for author in search['term']['include']:
                    q = q.where(ValueWrapper(author).isin(au_q))
                for author in search['term']['exclude']:
                    q = q.where(ValueWrapper(author).notin(au_q))
            elif search['type'] == 'tags':
                tag_q = MySQLQuery.from_(art_tags).select(art_tags.tag) \
                        .where(art_tags.article_id == art.id)
                for tag in search['term']['include']:
                    q = q.where(ValueWrapper(tag).isin(tag_q))
                for tag in search['term']['exclude']:
                    q = q.where(ValueWrapper(tag).notin(tag_q))
            elif search['type'] is None:
                q = q.where(
                    (art.title.like(search['term']))
                    | (art.scp_num == search['term'])
                )
            elif search['type'] == 'regex':
                q = q.where(art.title.regex(search['term']))
            elif search['type'] == 'url':
                q = q.where(art.url == search['term'])
        # query complete
        # insert custom functions
        q = str(q).replace(" LIKE ", " GLOB ")
        q = str(q).replace(" REGEX ", " REGEXP ")
        c = self.conn.cursor()
        print(str(q))
        c.execute(str(q))
        return c.fetchall()

DB = SqliteDriver()
