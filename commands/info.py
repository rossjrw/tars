"""info.py

Commands that output basic information about the bot.
"""

from datetime import timedelta
import time

import platform, distro

from helpers.basecommand import Command
from helpers.config import CONFIG
from helpers.error import CommandError
from helpers.greetings import acronym
from helpers.defer import defer

start_time = time.time()


class Help(Command):
    """Provides documentation for bot usage."""

    command_name = "help"
    defers_to = ["jarvis", "Secretary_Helen"]
    arguments = [
        dict(
            flags=['command'],
            type=str,
            nargs=None,
            help="""A command to get specific help for.

            Will link to that part of the documentation directly.
            """,
        )
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "Command documentation: https://git.io/TARS.help. Start a "
            "command with .. to force me to respond."
        )


class Status(Command):
    """Shows how long the bot has been alive for."""

    command_name = "status"

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "{} · run by {} · Python {} · {} · alive for {} · {}".format(
                acronym(),
                CONFIG.owner,
                platform.python_version(),
                " ".join(
                    distro.linux_distribution(full_distribution_name=True)[:2]
                ),
                timedelta(seconds=round(time.time() - start_time)),
                CONFIG.repository,
            )
        )


class Github(Command):
    """Links to the bot's repository."""

    arguments = [
        dict(
            flags=['section'],
            type=str,
            nargs=None,
            default="",
            choices=["i", "p"],
            help="""The part of the repository to link to.""",
        )
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "{}/{}".format(
                CONFIG['repository'],
                {'': "", 'i': "/issues", 'p': "/pulls"}[self['section']],
            )
        )


class User(Command):
    """Provides a link to a user's Wikidot page."""

    command_name = "user"
    defers_to = ["Secretary_Helen"]
    arguments = [
        dict(
            flags=['user'],
            type=str,
            nargs='+',
            required=True,
            help="""The name of the user.""",
        )
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "http://www.wikidot.com/user:info/{}".format(
                " ".join(self['user']).replace(" ", "-")
            )
        )


class Tag(Command):
    """Provides a link to a page that lists all articles with this tag.

    See also @command(tags), which is unrelated.
    """

    command_name = "tag"
    arguments = [
        dict(
            flags=['tag'],
            type=str,
            nargs=None,
            required=True,
            help="""The chosen tag.""",
        )
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "http://www.scp-wiki.wikidot.com/system:page-tags/tag/{}".format(
                self['tag']
            )
        )
