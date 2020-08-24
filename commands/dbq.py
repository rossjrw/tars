"""dbq.py

Database Query commands for checking the database.
"""

import string
from pprint import pprint
from datetime import datetime

import pendulum as pd

from commands.gib import gib
from helpers.error import CommandError, MyFaultError
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer


class query:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["table tables t", "user users u"])
        # No argument given - show the db structure
        if len(cmd.args) == 1:
            msg.reply(
                "https://raw.githubusercontent.com/"
                "rossjrw/tars/master/database.png"
            )
            return
        # Table - print a list of tables, or a given table
        if 'table' in cmd:
            if len(cmd['table']) > 0:
                # print a specific table
                msg.reply(
                    "Printing contents of table {} to console.".format(
                        cmd['table'][0]
                    )
                )
                DB.print_one_table(cmd['table'][0])
            else:
                # print a list of all tables
                tables = DB.get_all_tables()
                msg.reply(
                    "Printed a list of tables to console. {} total.".format(
                        len(tables)
                    )
                )
                print(" ".join(tables))
        # Users - print a list of users, or from a given channel
        if 'user' in cmd:
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
        if 'id' in cmd:
            # we want to find the id of something
            if len(cmd.args['root']) != 2:
                search = msg.sender
            else:
                search = cmd.args['root'][1]
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
        if 'alias' in cmd:
            search = (
                cmd.args['root'][1]
                if len(cmd.args['root']) > 1
                else msg.sender
            )
            aliases = DB.get_aliases(search)
            # should be None or a list of lists
            if aliases is None:
                msg.reply(
                    "I don't know anyone with the alias '{}'.".format(search)
                )
            else:
                msg.reply(
                    "I know {} users with the alias '{}'.".format(
                        len(aliases), search
                    )
                )
                for i, group in enumerate(aliases):
                    msg.reply("\x02{}.\x0F {}".format(i + 1, ", ".join(group)))
        if 'occ' in cmd:
            if len(cmd.args['root']) < 2:
                raise CommandError("Specify a channel to get the occupants of")
            msg.reply(
                "Printing occupants of {} to console".format(
                    cmd.args['root'][1]
                )
            )
            users = DB.get_occupants(cmd.args['root'][1], True)
            if isinstance(users[0], int):
                pprint(users)
            else:
                pprint([nickColor(user) for user in users])
        if 'sql' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            try:
                DB.print_selection(" ".join(cmd['sql']), 'str' in cmd)
                msg.reply("Printing that selection to console")
            except:
                msg.reply("There was a problem with the selection")
                raise


class seen:
    @staticmethod
    def command(irc_c, msg, cmd):
        if defer.check(cmd, 'Secretary_Helen'):
            return
        cmd.expandargs(["first f", "count c"])
        # have to account for .seen -f name
        if 'first' in cmd:
            cmd.args['root'].extend(cmd.args['first'])
        if 'count' in cmd:
            cmd.args['root'].extend(cmd.args['count'])
        if len(cmd.args['root']) < 1:
            raise CommandError(
                "Specify a user and I'll tell you when I last saw them"
            )
        nick = cmd.args['root'][0]
        messages = DB.get_messages_from_user(nick, msg.raw_channel)
        if len(messages) == 0:
            raise MyFaultError(
                "I've never seen {} in this channel.".format(nick)
            )
        if 'count' in cmd:
            msg.reply(
                "I've seen {} {} times in this channel.".format(
                    nick, len(messages)
                )
            )
            return
        if 'first' in cmd:
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
            gib.obfuscate(
                message['message'], DB.get_channel_members(msg.raw_channel)
            ),
        )
        msg.reply(response)
