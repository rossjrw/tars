"""record.py

For recording and uploading message transcripts.
"""
from datetime import datetime
import string

from pyaib.signals import await_signal

# from helpers.api import Topia
from helpers.database import DB
from helpers.defer import defer
from helpers.error import CommandError, MyFaultError
from helpers.parse import nickColor

IS_RECORDING = False


class pingall:
    @classmethod
    def execute(cls, irc_c, msg, cmd):
        """Ping everyone in the channel"""
        cmd.expandargs(
            [
                "message msg m",  # message to be PM'd
                "target t",  # channel op level target
                "channel c",  # channel to get names from
                "help h",
            ]
        )

        # TODO remove this check in the argparse refactor
        if len(cmd.args['root']) > 0 or 'help' in cmd:
            raise CommandError(
                "Usage: ..pingall [--target level] [--message "
                "message]. If -m is not set, ping will happen "
                "in this channel. If -m is set, message will "
                "be sent to users in PM."
            )

        # TODO extend this to channel operator
        if not defer.controller(cmd):
            raise CommandError("You're not authorised to do that")

        cmd.expandargs(["channel c"])
        if 'channel' in cmd:
            if not defer.controller(cmd):
                raise MyFaultError(
                    "You're not authorised to extract the "
                    "nicks of another channel"
                )
            channel = cmd['channel'][0]
        else:
            channel = msg.raw_channel
        if 'target' in cmd:
            if len(cmd['target']) != 1:
                raise CommandError(
                    "Specify a target as a channel user mode "
                    "symbol: one of +, %, @, &, ~"
                )
            if not cmd['target'][0] in '+%@&~' and len(cmd['target'][0]) == 1:
                raise CommandError(
                    "When using the --target/-t argument, the "
                    "target must be a channel user mode: one "
                    "of +, %, @, &, ~"
                )
        # Issue a fresh NAMES request and await the response
        defer.get_users(irc_c, channel)
        try:
            response = await_signal(irc_c, 'NAMES_RESPONSE', timeout=5.0)
            # returned data is the channel name
            assert response == channel
        except (TimeoutError, AssertionError):
            # response to success/failure is the same, so doesn't matter
            pass
        finally:
            members = DB.get_occupants(channel, True, levels=True)
        if 'target' in cmd:
            modes = '+%@&~'
            members = [
                nick
                for nick, mode in members
                if mode is not None
                and modes.find(mode) >= modes.find(cmd['target'][0])
            ]
        else:
            members = [nick for nick, mode in members]
        if 'message' in cmd:
            message = " ".join(cmd.args['message'])
            for member in members:
                irc_c.PRIVMSG(
                    member,
                    "{} (from {} in {})".format(
                        " ".join(cmd.args['root']), msg.sender, msg.raw_channel
                    ),
                )
            msg.reply("Message sent to selected users.")
        else:
            msg.reply("{}: ping!".format(", ".join(members)))


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
    def execute(cls, irc_c, msg, cmd):
        """Record and broadcast messages"""
        if not defer.controller(cmd):
            raise CommandError("You're not authorised to do that")
        raise MyFaultError("The .record command is currently disabled.")
        cmd.expandargs(["output o", "format f", "restrict-channel-name"])
        # get the action - start, stop or status
        if len(cmd.args['root']) == 0:
            raise CommandError(
                "Usage: .record [start|stop|status|page] "
                "[--output location] [--format format]"
            )
        if len(cmd.args['root']) > 1:
            raise CommandError("Only one action can be taken at a time.")
        action = cmd.args['root'][0]
        if action == 'page':
            msg.reply(
                "Output page: http://topia.wikidot.com/tars:recording-output"
            )
            return
        if action == 'status':
            if msg.raw_channel in cls.recording_channels():
                msg.reply(
                    "Currently recording in this channel. "
                    "Use `.record stop` to stop the recording."
                )
            else:
                msg.reply("Not currently recording in this channel.")
            if defer.controller(cmd) and msg.raw_channel is None:
                # if a controller asks in pm, show all channels
                msg.reply(
                    "Currently recording in: {}".format(
                        ", ".join(
                            [
                                s['channel']
                                for s in cls.settings
                                if s['recording']
                            ]
                        )
                    )
                )
            return
        elif action == 'start':
            if msg.raw_channel is None:
                raise CommandError("You can't record PMs.")
            if msg.raw_channel in cls.recording_channels():
                raise CommandError(
                    "Already recording in {}".format(msg.raw_channel)
                )
            else:
                msg.reply(
                    "Starting recording messages in {}".format(msg.raw_channel)
                )
                if 'restrict-channel-name' in cmd:
                    msg.reply("I will hide the channel name from the output.")
        elif action == 'stop':
            if msg.raw_channel not in cls.recording_channels():
                raise CommandError(
                    "Not recording in {}".format(msg.raw_channel)
                )
            else:
                msg.reply("Stopping recording in {}".format(msg.raw_channel))
                if 'restrict-channel-name' in cmd:
                    msg.reply("I will hide the channel name from the output.")
        else:
            raise CommandError("Action must be one of start, stop, status")
        # get arguments and save to vars
        output_location = None
        if 'output' in cmd:
            if cmd['output'][0] not in ['topia', 'here', 'both']:
                raise CommandError(
                    "Output location must be topia, here or both"
                )
            output_location = cmd['output'][0]
        output_format = None
        if 'format' in cmd:
            if cmd['format'][0] not in ['json', 'txt', 'ftml']:
                raise CommandError("Format type must be json, txt or ftml")
            output_format = cmd['format'][0]

        # after everything else, set this channel as recording or not
        if action == 'start':
            # get the most recent message id in this channel
            start_id = DB.get_most_recent_message(msg.raw_channel)
            # add this channel to the settings list
            cls.settings.append(
                {
                    'channel': msg.raw_channel,
                    'recording': True,
                    'location': output_location,
                    'format': output_format,
                    'start_id': start_id,
                    'hide': 'restrict-channel-name' in cmd,
                }
            )
        if action == 'stop':
            sett = [
                s for s in cls.settings if s['channel'] == msg.raw_channel
            ][0]
            end_id = DB.get_most_recent_message(msg.raw_channel)
            messages = DB.get_messages_between(
                msg.raw_channel, sett['start_id'], end_id
            )
            if sett['location'] in ['topia', None]:
                msg.reply(
                    "Uploading {} messages to topia...".format(len(messages))
                )
                # get page content
                page = Topia.get_page({'page': "tars:recording-output"})
                content = page['content']
                content += "\r\n\r\n====\r\n\r\n"
                content += "+ Recording on {} from {}".format(
                    datetime.today().strftime('%Y-%m-%d'),
                    sett['channel'] if not sett['hide'] else "[REDACTED]",
                )
                content += "\r\n\r\n"
                for message in messages:
                    if message['kind'] == 'PRIVMSG':
                        content += "||~ {} ||~ ##{}|{}## || {} ||".format(
                            (
                                datetime.fromtimestamp(
                                    message['timestamp']
                                ).strftime("%H:%M:%S")
                            ),
                            nickColor(message['sender'], True),
                            message['sender'],
                            message['message'].replace("||", "@@||@@"),
                        )
                    elif message['kind'] == 'NICK':
                        content += "||~ {} ||||~ ##{}|{}## → ##{}|{}## ||".format(
                            (
                                datetime.fromtimestamp(
                                    message['timestamp']
                                ).strftime("%H:%M:%S")
                            ),
                            nickColor(message['sender'], True),
                            message['sender'],
                            nickColor(message['message'], True),
                            message['message'],
                        )
                    elif message['kind'] in ['JOIN', 'PART', 'QUIT']:
                        content += "||~ {} ||||~ {} ##{}|{}## {} ||".format(
                            (
                                datetime.fromtimestamp(
                                    message['timestamp']
                                ).strftime("%H:%M:%S")
                            ),
                            "→" if message['kind'] == 'JOIN' else "←",
                            nickColor(message['sender'], True),
                            message['sender'],
                            "joined" if message['kind'] == 'JOIN' else "left",
                        )
                    else:
                        content += "|||||| Error code {} ||".format(
                            message['id']
                        )
                    content += "\r\n"
                content += "\r\n"
                okchars = string.printable + "→←"
                content = "".join(filter(lambda x: x in okchars, content))
                # then format for wikidot
                # TODO save the content somewhere
                msg.reply(
                    "Done! http://topia.wikidot.com/tars:recording-output"
                )
            else:
                raise MyFaultError("Unknown location")
            cls.settings.remove(sett)
            # upload either to here or to wikidot

    @classmethod
    def recording_channels(cls):
        return [s['channel'] for s in cls.settings if s['recording']]
