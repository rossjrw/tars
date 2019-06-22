"""dbq.py

Database Query commands for checking the database.
"""

from pprint import pprint
from helpers.error import CommandError
from helpers.parse import nickColor

class alias:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        pass

class query:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) == 0:
            msg.reply("https://raw.githubusercontent.com/"
                      "rossjrw/tars/master/database.png")
            return
        if cmd.args['root'][0].startswith('table'):
            if len(cmd.args['root']) >= 2:
                # print a specific table
                msg.reply("Printing contents of table {} to console."
                          .format(cmd.args['root'][1]))
                irc_c.db._driver.print_one_table(cmd.args['root'][1])
            else:
                # print a list of all tables
                tables = irc_c.db._driver.get_all_tables()
                msg.reply("Printed a list of tables to console. {} total."
                          .format(len(tables)))
                print(" ".join(tables))
        elif cmd.args['root'][0] == 'users':
            users = irc_c.db._driver.get_all_users()
            if len(users) == 0:
                msg.reply("There are no users.")
            elif len(users) < 15:
                msg.reply(", ".join(users))
            else:
                msg.reply("Printed a list of users to console. {} total."
                          .format(len(users)))
                print(" ".join([nickColor(u) for u in users]))
        elif cmd.args['root'][0] == 'id':
            # we want to find the id of something
            if len(cmd.args['root']) != 2:
                search = msg.sender
            else:
                search = cmd.args['root'][1]
            id,type = irc_c.db._driver.get_generic_id(search)
            if id:
                if type == 'user' and search == msg.sender:
                    msg.reply("{}, your ID is {}.".format(msg.sender, id))
                elif search == "TARS":
                    msg.reply("My ID is {}.".format(id))
                else:
                    msg.reply("{}'s ID is {}.".format(search, id))
            else:
                if type == 'channel':
                    msg.reply("I don't know the channel '{}'."
                             .format(search))
                else:
                    msg.reply("I don't know anything called '{}'."
                              .format(search))
        elif cmd.args['root'][0].startswith('alias'):
            search = cmd.args['root'][1] if len(cmd.args['root']) > 1 \
                                         else msg.sender
            aliases = irc_c.db._driver.get_aliases(search)
            # should be None or a list of lists
            if aliases is None:
                msg.reply("I don't know anyone with the alias '{}'."
                          .format(search))
            else:
                msg.reply("I know {} users with the alias '{}'."
                          .format(len(aliases), search))
                for i,group in enumerate(aliases):
                    msg.reply("\x02{}.\x0F {}"
                              .format(i+1, ", ".join(group)))
        elif cmd.args['root'][0].startswith('occ'):
            if len(cmd.args['root']) < 2:
                raise CommandError("Specify a channel to get the occupants of")
            msg.reply("Printing occupants of {} to console"
                      .format(cmd.args['root'][1]))
            users = irc_c.db._driver.get_occupants(cmd.args['root'][1], True)
            if isinstance(users[0], int):
                pprint(users)
            else:
                pprint([nickColor(user) for user in users])
        else:
            raise CommandError("Unknown argument")
