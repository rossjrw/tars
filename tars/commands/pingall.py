"""pingall.py

Pings everyone in the room.
"""

from pyaib.signals import await_signal

from tars.helpers.basecommand import Command, matches_regex
from tars.helpers.database import DB
from tars.helpers.defer import defer
from tars.helpers.error import CommandError, MyFaultError


class Pingall(Command):
    """Pings everyone in the room.

    Just dumps a list of everyone's names into the channel. Can also be used to
    send a message to everyone in the room.
    """

    command_name = "Ping everyone"
    aliases = ["pingall"]
    arguments = [
        dict(
            flags=['--message', '-m'],
            type=str,
            nargs='+',
            help="""Specify a message to be PMed to everyone.

            When this option is added, instead of pinging everyone, TARS will
            send a private message to everyone. The message will include your
            name as well as the current channel.
            """,
        ),
        dict(
            flags=['--channel'],
            type=matches_regex("^#", "must be a channel"),
            mode='hidden',
            help="""The channel for the NAMES request.""",
        ),
        dict(
            flags=['--target', '-t'],
            type=str,
            nargs=None,
            default="",
            choices=["~", "&", "@", "%", "+"],
            help="""The op level target.

            Use this argument to restrict who is pinged by their op level in
            the channel.

            @example(..pingall -t @)(pings all operators in the channel, and
            all ranks above that (admins and owners).)

            The choices are the same as the symbols used on IRC:

            * `~` &mdash; Channel owners.
            * `&` &mdash; Channel admins and above.
            * `@` &mdash; Channel operators and above.
            * `%` &mdash; Channel half-ops and above.
            * `+` &mdash; Voiced users (and all users with a role).
            """,
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        # TODO extend this to channel operator (or at least voiced)
        if not defer.controller(cmd):
            raise CommandError("You're not authorised to do that")

        if 'channel' in self:
            if not defer.controller(cmd):
                raise MyFaultError(
                    "You're not authorised to extract the "
                    "nicks of another channel"
                )
            channel = self['channel']
        else:
            channel = msg.raw_channel
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
        modes = "+%@&~"
        members = [
            nick
            for nick, mode in members
            if mode is not None
            and modes.find(mode) >= modes.find(self['target'])
            # Unspecified target is "" so this is genius honestly
        ]
        if len(self['message']) > 0:
            for member in members:
                irc_c.PRIVMSG(
                    member,
                    "{1} in {2} says: {0}".format(
                        " ".join(self['message']), msg.sender, msg.raw_channel
                    ),
                )
            msg.reply("Message sent to selected users.")
        else:
            msg.reply("{}: ping!".format(", ".join(members)))
