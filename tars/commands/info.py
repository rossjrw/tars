"""info.py

Commands that output basic information about the bot.
"""

from datetime import timedelta
import time

import platform, distro

# from tars.commands import COMMANDS_REGISTRY
from tars.helpers.basecommand import Command
from tars.helpers.config import CONFIG
from tars.helpers.error import CommandError, MyFaultError
from tars.helpers.greetings import acronym

start_time = time.time()


class Help(Command):
    """Provides documentation for bot usage.

    Will provide a link to this page. You can also choose to get more specific
    help by specifying a command alias, in which case it will give a brief
    overview of the command with that alias and then link to its specific
    documentation. The link is the same as those that can be found in this
    page's sidebar.
    """

    command_name = "Help"
    aliases = ["help"]
    arguments = [
        dict(
            flags=['alias'],
            type=str,
            nargs='?',
            default="",
            help="""A command to get specific help for.

            Gives a brief overview of the command with this alias followed by a
            link to that command's full documentation. The argument can be
            preceded by leading dots or not, it doesn't matter.

            @example(..help search)(shows help for @command(search).)

            You can also do this by adding the `-?`, `-h` or `--help` argument to
            _any_ command, for example @example(..search --help).
            """,
        ),
        dict(
            flags=['argument'],
            type=str,
            nargs='?',
            default="",
            mode='hidden',
            help="""An argument of the given command to get specific help for.

            Gives a brief overview of the argument followed by a link to that
            argument's full documentation. The argument can be preceded by
            leading hyphens or not, it doesn't matter.

            @example(..help help argument)(shows help for this command's
            @argument(argument) argument.)
            """,
        ),
    ]

    full_docs = "Full documentation: {}".format(CONFIG['documentation'])
    specific_docs = "Documentation: {}#{{}}".format(CONFIG['documentation'])

    def execute(self, irc_c, msg, cmd):
        if self['alias'] == "":
            msg.reply(
                "{}. Start a command with .. to force me to respond.".format(
                    Help.full_docs
                )
            )
            return
        self['alias'] = self['alias'].strip(".")
        self['argument'] = self['argument'].strip("-")
        # If a command has been specified, link to specific help for it
        # TODO This only handles commands/arguments with a defined name and
        # docstring for now
        anchor = Help.anchor(self['alias'], self['argument'])
        if len(anchor) == 0:
            raise MyFaultError(
                "I have no commands with the alias '{}'. {}".format(
                    self['alias'], Help.full_docs
                )
            )
        if self['argument'] == "":
            # Command specified, argument not specified
            msg.reply(
                "{}: {} {}".format(
                    anchor[0].command_name,
                    anchor[0].get_intro(),
                    Help.specific_docs.format(anchor[0].__name__.lower()),
                )
            )
        else:
            # Command specified, argument specified
            if len(anchor) == 1:
                raise MyFaultError(
                    "{} doesn't have an argument named '{}'. {}".format(
                        anchor[0].command_name,
                        self['argument'],
                        Help.specific_docs.format(anchor[0].__name__.lower()),
                    )
                )
            msg.reply(
                "{} / {}: {} {}".format(
                    anchor[0].command_name,
                    anchor[1]['flags'][0],
                    anchor[0].get_intro(argument=anchor[1]),
                    Help.specific_docs.format(
                        "-".join(
                            [
                                anchor[0].__name__.lower(),
                                anchor[1]['flags'][0].strip("-"),
                            ]
                        )
                    ),
                )
            )

    @staticmethod
    def anchor(alias, argument=None):
        """Makes the anchor that will link to the given command or the given
        argument.

        Returns a tuple of length 0 if the command does not exist, length 1 if
        the command exists but the argument doesn't, and length 2 if they both
        exist. The first item is the command class, the second item is the
        argument.
        """
        from tars.commands import COMMANDS_REGISTRY

        try:
            command = COMMANDS_REGISTRY.get_command_by_alias(alias)
        except KeyError:
            return ()
        if argument is None:
            return (command,)
        argument = command.get_argument(argument)
        if argument is None:
            return (command,)
        return (command, argument)


class Status(Command):
    """Shows how long the bot has been alive for."""

    command_name = "Status"
    aliases = ["status", "tars"]

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

    aliases = ["github", "gh"]
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

    command_name = "Link to user"
    aliases = ["user"]
    arguments = [
        dict(
            flags=['user'],
            type=str,
            nargs='+',
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

    command_name = "List tagged"
    aliases = ["tag"]
    arguments = [
        dict(flags=['tag'], type=str, nargs=None, help="""The chosen tag.""",)
    ]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "http://www.scp-wiki.wikidot.com/system:page-tags/tag/{}".format(
                self['tag']
            )
        )
