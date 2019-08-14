"""dbq.py

Database Query commands for checking the database.
"""

from pprint import pprint
from datetime import datetime
from helpers.error import CommandError
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer
from helpers.api import Topia

IS_RECORDING = False

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
                DB.print_one_table(cmd.args['root'][1])
            else:
                # print a list of all tables
                tables = DB.get_all_tables()
                msg.reply("Printed a list of tables to console. {} total."
                          .format(len(tables)))
                print(" ".join(tables))
        elif cmd.args['root'][0] == 'users':
            users = DB.get_all_users()
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
            id,type = DB.get_generic_id(search)
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
            aliases = DB.get_aliases(search)
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
            users = DB.get_occupants(cmd.args['root'][1], True)
            if isinstance(users[0], int):
                pprint(users)
            else:
                pprint([nickColor(user) for user in users])
        elif cmd.args['root'][0].startswith('sql'):
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            try:
                DB.print_selection(" ".join(cmd.args['root'][1:]))
                msg.reply("Printing that selection to console")
            except:
                msg.reply("There was a problem with the selection")
                raise
        else:
            raise CommandError("Unknown argument")

class record:
    settings = []
    # settings is a list of dicts of keys:
        # channel: name of channel
        # recording: are we currently recording in this channel?
        # location: output location? default None (topia, here, both)
        # format: output format? default None (json, txt, ftml)
        # start_id: the ID of the 1st message in the recording
    @classmethod
    def command(cls, irc_c, msg, cmd):
        """Record and broadcast messages"""
        if not defer.controller(cmd):
            raise CommandError("You're not authorised to do that")
        cmd.expandargs(["output o",
                        "format f"])
        # get the action - start, stop or status
        if len(cmd.args['root']) == 0:
            raise CommandError("Usage: .record [start|stop|status] "
                               "[--output location] [--format format]")
        if len(cmd.args['root']) > 1:
            raise CommandError("Only one action can be taken at a time.")
        action = cmd.args['root'][0]
        if action == 'status':
            if msg.channel in cls.recording_channels():
                msg.reply("Currently recording in this channel. "
                          "Use `.record stop` to stop the recording.")
            else:
                msg.reply("Not currently recording in this channel.")
            if defer.controller(cmd) and msg.channel is None:
                # if a controller asks in pm, show all channels
                msg.reply("Currently recording in: {}".format(", ".join(
                    [s['channel'] for s in settings if s['recording']])))
            return
        elif action == 'start':
            if msg.channel is None:
                raise CommandError("You can't record PMs.")
            if msg.channel in cls.recording_channels():
                raise CommandError("Already recording in {}"
                                   .format(msg.channel))
            else:
                msg.reply("Starting recording messages in {}"
                          .format(msg.channel))
        elif action == 'stop':
            if msg.channel not in cls.recording_channels():
                raise CommandError("Not recording in {}"
                                   .format(msg.channel))
            else:
                msg.reply("Stopping recording in {}"
                          .format(msg.channel))
        else:
            raise CommandError("Action must be one of start, stop, status")
        # get arguments and save to vars
        output_location = None
        if cmd.hasarg('output'):
            if cmd.getarg('output') not in ['topia', 'here', 'both']:
                raise CommandError("Output location must be topia, here or both")
            output_location = cmd.getarg('output')
        output_format = None
        if cmd.hasarg('format'):
            if cmd.getarg('format') not in ['json', 'txt', 'ftml']:
                raise CommandError("Format type must be json, txt or ftml")
            output_format = cmd.getarg('format')

        # after everything else, set this channel as recording or not
        if action == 'start':
            # get the most recent message id in this channel
            start_id = DB.get_most_recent_message(msg.channel)
            # add this channel to the settings list
            cls.settings.append({'channel': msg.channel,
                                 'recording': True,
                                 'location': output_location,
                                 'format': output_format,
                                 'start_id': start_id})
        if action == 'stop':
            sett = [s for s in settings if s['channel'] == msg.channel][0]
            end_id = DB.get_most_recent_message(msg.channel)
            messages = DB.get_messages_between(msg.channel, sett['start_id'], end_id)
            msg.reply("Uploading {} messages to {}..."
                      .format(len(messages), s['location']))
            if s['location'] in ['topia', None]:
                # get page content
                page = Topia.get_page({'page':"tars:recording-output"})
                content = page['content']
                content += "\n\n====\n\n"
                content += "+ Recording on {} from {}".format(
                    datetime.today().strftime('%Y-%m-%d'),
                    msg.channel if not hide else "[REDACTED]")
                content += "\n\n"
                # then format for wikidot
                # TODO nickColor as html codes
                # copy log beautifier
            # upload either to here or to wikidot

    @classmethod
    def recording_channels(cls):
        return [s['channel'] for s in settings if s['recording']]
