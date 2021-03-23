"""dbq.py

Database Query commands for checking the database.
"""

import string
from pprint import pprint
from datetime import datetime

import pendulum as pd

from tars.commands.gib import Gib
from tars.helpers.basecommand import Command
from tars.helpers.error import CommandError, MyFaultError
from tars.helpers.parse import nickColor
from tars.helpers.database import DB
from tars.helpers.defer import defer


class Query(Command):
    """For checking the integrity of the database.

    This command does not result in any meaningful output in IRC beyond
    confirmation of the command. Instead, information is printed to the bot's
    console.
    """

    aliases = ["dbq"]
    arguments = [
        dict(
            flags=['--tables'],
            type=str,
            nargs='?',
            help="""Examine the tables in the database.

            Accepts the name of the table to print. If no name is provided,
            prints a list of tables.
            """,
        ),
        dict(
            flags=['--users'],
            type=bool,
            help="""Prints a list of known users.""",
        ),
        dict(
            flags=['--id'],
            type=str,
            nargs='?',
            help="""Gets the ID of a thing.

            The thing can be a user or a channel. If no argument is provided,
            the thing is assumed to be yourself.
            """,
        ),
        dict(
            flags=['--sql'],
            type=str,
            nargs='+',
            help="""Issue an SQL statement to the database.

            This should only be used for read-only queries. @command(refactor)
            should be used for statements that modify the database.
            """,
        ),
        dict(
            flags=['--str'],
            type=bool,
            help="""Print SQL results as a string rather than a table.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        if 'tables' in self:
            if self['tables'] is not None:
                # print a specific table
                msg.reply(
                    "Printing contents of table {} to console.".format(
                        self['tables']
                    )
                )
                DB.print_one_table(self['tables'])
            else:
                # print a list of all tables
                tables = DB.get_all_tables()
                msg.reply(
                    "Printed a list of tables to console. {} total.".format(
                        len(tables)
                    )
                )
                print(" ".join(tables))
        elif self['users']:
            users = DB.get_all_users()
            if len(users) == 0:
                msg.reply("There are no users.")
            else:
                msg.reply(
                    "Printed a list of users to console. {} total.".format(
                        len(users)
                    )
                )
                print(" ".join([nickColor(u) for u in users]))
        elif 'id' in self:
            # we want to find the id of something
            if self['id'] is None:
                search = msg.sender
            else:
                search = self['id']
            id, type = DB.get_generic_id(search)
            if id:
                if type == 'user' and search == msg.sender:
                    msg.reply("{}, your ID is {}.".format(msg.sender, id))
                elif search == "TARS":
                    msg.reply("My ID is {}.".format(id))
                else:
                    msg.reply("{}'s ID is {}.".format(search, id))
            else:
                if type == 'channel':
                    msg.reply("I don't know the channel '{}'.".format(search))
                else:
                    msg.reply(
                        "I don't know anything called '{}'.".format(search)
                    )
        elif len(self['sql']) > 0:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            try:
                DB.print_selection(" ".join(self['sql']), 'str' in self)
                msg.reply("Printing that selection to console")
            except:
                msg.reply("There was a problem with the selection")
                raise
        else:
            msg.reply("Checking... yes! There is a database.")


class Seen(Command):
    """Check when the bot last saw a given user.

    For privacy reasons, only checks the current channel.
    """

    command_name = "Last seen"
    aliases = ["seen", "lastseen"]
    arguments = [
        dict(
            flags=['nick'],
            type=str,
            nargs='?',
            help="""The nick of the user to search for.

            Aliases of this user will also be searched for.

            When using @argument(first) or @argument(count), the nick can be
            omitted here, in which case a nick is expected at the end of the
            command.
            """,
        ),
        dict(
            flags=['--first', '-f'],
            type=str,
            nargs='?',
            metavar="nick",
            help="""Shows when the user was first seen.

            The username can come after this argument, in which case it
            overrides a username that was provided before it.
            """,
        ),
        dict(
            flags=['--count', '-c'],
            type=str,
            nargs='?',
            metavar="nick",
            help="""Counts the number of times this user has been seen.

            The username can come after this argument, in which case it
            overrides a username that was provided before it.
            """,
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        nick = self['nick']
        if 'first' in self and self['first'] is not None:
            nick = self['first']
        if 'count' in self and self['count'] is not None:
            nick = self['count']
        if nick is None:
            raise CommandError(
                "Specify a user and I'll tell you when I last saw them"
            )
        messages = DB.get_messages_from_user(nick, msg.raw_channel)
        if len(messages) == 0:
            raise MyFaultError(
                "I've never seen {} in this channel.".format(nick)
            )
        if 'count' in self:
            msg.reply(
                "I've seen {} {} times in this channel.".format(
                    nick, len(messages)
                )
            )
            return
        if 'first' in self:
            message = messages[0]
            response = "I first saw {} {} saying: {}"
        else:
            if nick == msg.sender:
                msg.reply("I can see you right now, {}.".format(msg.sender))
                return
            message = messages[-1]
            response = "I last saw {} {} saying: {}"
        response = response.format(
            nick
            if nick == message['sender']
            else "{} as {}".format(nick, message['sender']),
            pd.from_timestamp(message['timestamp']).diff_for_humans(),
            Gib.obfuscate(
                message['message'], DB.get_channel_members(msg.raw_channel)
            ),
        )
        msg.reply(response)
