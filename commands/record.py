"""record.py

For recording and uploading message transcripts.
"""
import string
from pprint import pprint
from datetime import datetime
from helpers.error import CommandError
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer
from helpers.api import Topia

IS_RECORDING = False

class record:
    settings = []
    # settings is a list of dicts of keys:
        # channel: name of channel
        # recording: are we currently recording in this channel?
        # location: output location? default None (topia, here, both)
        # format: output format? default None (json, txt, ftml)
        # start_id: the ID of the 1st message in the recording
        # hide: hide channel name at output?
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
                    [s['channel'] for s in cls.settings if s['recording']])))
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
        if 'output' in cmd:
            if cmd['output'] not in ['topia', 'here', 'both']:
                raise CommandError("Output location must be topia, here or both")
            output_location = cmd['output']
        output_format = None
        if 'format' in cmd:
            if cmd['format'] not in ['json', 'txt', 'ftml']:
                raise CommandError("Format type must be json, txt or ftml")
            output_format = cmd['format']

        # after everything else, set this channel as recording or not
        if action == 'start':
            # get the most recent message id in this channel
            start_id = DB.get_most_recent_message(msg.channel)
            # add this channel to the settings list
            cls.settings.append({'channel': msg.channel,
                                 'recording': True,
                                 'location': output_location,
                                 'format': output_format,
                                 'start_id': start_id,
                                 'hide': 'restrict-channel-name' in cmd})
        if action == 'stop':
            sett = [s for s in cls.settings if s['channel'] == msg.channel][0]
            end_id = DB.get_most_recent_message(msg.channel)
            messages = DB.get_messages_between(msg.channel, sett['start_id'], end_id)
            msg.reply("Uploading {} messages to {}..."
                      .format(len(messages), sett['location']))
            if sett['location'] in ['topia', None]:
                # get page content
                page = Topia.get_page({'page':"tars:recording-output"})
                content = page['content']
                content += "\r\n\r\n====\r\n\r\n"
                content += "+ Recording on {} from {}".format(
                    datetime.today().strftime('%Y-%m-%d'),
                    sett['channel'] if not sett['hide'] else "[REDACTED]")
                content += "\r\n\r\n"
                for message in messages:
                    if message['kind'] == 'PRIVMSG':
                        content += "||~ {} ||~ ##{}|{}## || {} ||".format(
                            (datetime.fromtimestamp(message['timestamp'])
                                     .strftime("%H:%M:%S")),
                            nickColor(message['sender'], True),
                            message['sender'],
                            message['message'])
                    if message['kind'] == 'NICK':
                        content += "||~ {} ||||~ {} → {} ||".format(
                            (datetime.fromtimestamp(message['timestamp'])
                                     .strftime("%H:%M:%S")),
                            message['sender'],
                            message['message'])
                    if message['kind'] == 'NICK':
                        content += "||~ {} ||||~ {} {} ||".format(
                            (datetime.fromtimestamp(message['timestamp'])
                                     .strftime("%H:%M:%S")),
                            message['sender'],
                            "joined" if message['kind'] is 'JOIN' else "left")
                    content += "\r\n"
                content += "\r\n"
                content = "".join(filter(lambda x: x in string.printable, content))
                # then format for wikidot
                # TODO nickColor as html codes
                # copy log beautifier
                print(content)
                Topia.save_page({'page':"tars:recording-output",
                                 'content': content,
                                 'revision_comment': "New recording",
                                 'notify_watchers': "true"})
            cls.settings.remove(sett)
            # upload either to here or to wikidot

    @classmethod
    def recording_channels(cls):
        return [s['channel'] for s in cls.settings if s['recording']]
