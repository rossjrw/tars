"""pingall.py

Pings everyone in the room.
"""

from pyaib.signals import await_signal

from helpers.database import DB
from helpers.defer import defer
from helpers.error import CommandError, MyFaultError


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
