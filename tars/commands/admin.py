"""admin.py

A bunch of commands for Controllers to use.
"""

import os
import sys

import git
from tars.commands.gib import Gib
from tars.helpers.basecommand import Command, longstr, matches_regex
from tars.helpers.database import DB
from tars.helpers.error import CommandError
from tars.helpers.greetings import kill_bye


class Kill(Command):
    """Shut down the bot."""

    command_name = "Kill"
    aliases = ["kill", "kys"]
    permission = True

    def execute(self, irc_c, msg, cmd):
        msg.reply(kill_bye())
        irc_c.RAW("QUIT See you on the other side")
        irc_c.client.die()


class Join(Command):
    """Have the bot join a channel.

    All channels that the bot joins are added to its autojoin list, so you will
    only need to use this command once. In the future, this command may become
    restricted to users with elevated permissions.
    """

    command_name = "Join a channel"
    aliases = ["join", "rejoin"]
    arguments = [
        dict(
            flags=['channel'],
            type=matches_regex(r"^#", "must be a channel"),
            nargs=None,
            help="""The channel to join.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        # Note that the INVITE event is in plugins/parsemessages.py
        irc_c.JOIN(self['channel'])
        msg.reply("Joining {}".format(self['channel']))
        irc_c.PRIVMSG(
            self['channel'], "Joining by request of {}".format(msg.nick)
        )
        DB.join_channel(self['channel'])


class Leave(Command):
    """Have the bot leave a channel.

    This is the only way to make the bot leave your channel for good. Just
    kicking it will not work, as it will come back when it is rebooted.
    """

    command_name = "Leave a channel"
    aliases = ["leave", "part"]
    arguments = [
        dict(
            flags=['channel'],
            type=matches_regex(r"^#", "must be a channel"),
            nargs='?',
            help="""The channel to leave.

            If not provided, defaults to the channel that the command was used
            in.
            """,
        ),
        dict(
            flags=['--message', '-m'],
            type=longstr,
            nargs='+',
            help="""The message to leave on departure.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        if 'message' in self:
            leavemsg = self['message']
        else:
            leavemsg = None
        if self['channel'] is not None:
            channel = self['channel']
            msg.reply("Leaving {}".format(self['channel']))
        else:
            channel = msg.raw_channel
        irc_c.PART(channel, message=leavemsg)
        DB.leave_channel(channel)


class Reload(Command):
    """Reload the bot's commands."""

    command_name = "Reload"
    aliases = ["reload"]

    def execute(self, irc_c, msg, cmd):
        # do nothing - this is handled by parsemessage
        pass


class Reboot(Command):
    """Reboots the whole bot."""

    command_name = "Reboot"
    aliases = ["reboot"]
    permission = True

    def execute(self, irc_c, msg, cmd):
        msg.reply("Rebooting...")
        irc_c.RAW("QUIT Rebooting, will be back soon!")
        os.execl(sys.executable, sys.executable, *sys.argv)


class Update(Command):
    """Update the bot from the Git repository."""

    command_name = "Update"
    aliases = ["update"]
    permission = True

    def execute(self, irc_c, msg, cmd):
        msg.reply("Updating...")
        try:
            g = git.cmd.Git(".")
            g.pull()
        except Exception:
            msg.reply("Update failed.")
            raise
        msg.reply("Update successful - now would be a good time to reboot.")


class Say(Command):
    """Make the bot send a message somewhere.

    @example(..say #tars hello there!)(make the bot say "hello there!" in
    `#tars`.)
    """

    aliases = ["say"]
    permission = True
    arguments = [
        dict(
            flags=['recipient'],
            type=matches_regex(
                r"^(#|[A-z0-9])", "must be a channel or a user"
            ),
            nargs=None,
            help="""Where to send the message. Either a channel or a user.""",
        ),
        dict(
            flags=['message'],
            type=str,
            nargs='+',
            help="""The content of the message.

            If the message starts with `/`, it will sent as a raw message i.e.
            executed as a command. The recipient must be the current channel,
            as a safety check. Bear in mind that the commands available via
            this method are not the same as those available via the user
            interface. For example, the command to send a message is not 'msg'
            but 'PRIVMSG'.""",
        ),
        dict(
            flags=['--obfuscate', '-o'],
            type=bool,
            help="""Obfuscate any nick pings in the message.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        message = " ".join(self['message'])
        if message.startswith("/"):
            if msg.raw_channel != self['recipient']:
                raise CommandError(
                    "When executing a command with ..say, the recipient must "
                    "be the current channel ({}), as a safety check.".format(
                        msg.raw_channel
                    )
                )
            # This is an IRC command
            msg.reply("Issuing that...")
            # Send the message without the leading slash
            irc_c.RAW(message[1:])
        else:
            if self['obfuscate'] and msg.raw_channel is not None:
                message = Gib.obfuscate(
                    message, DB.get_aliases(None) + ["ops"]
                )
            irc_c.PRIVMSG(self['recipient'], message)
            if self['recipient'] != msg.raw_channel:
                msg.reply("Saying that to {}".format(self['recipient']))


class Config(Command):
    aliases = ["config"]

    def execute(self, irc_c, msg, cmd):
        msg.reply("http://scp-sandbox-3.wikidot.com/collab:tars")
        # TODO update this to final page (or src from .conf?)


class Debug(Command):
    """Debug command"""

    aliases = ["debug"]

    arguments = [
        dict(
            flags=["--longstr"],
            type=longstr,
            nargs='*',
            help="""Long string.""",
        ),
        dict(
            flags=["--restricted"],
            permission=True,
            type=bool,
            help="""This argument has elevated permissions.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(self['longstr'])
