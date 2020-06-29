"""info.py

Commands that output basic information about the bot.
"""

from helpers.error import CommandError
from helpers.greetings import acronym
from helpers.scheduler import uptime
from helpers.defer import defer
import platform, distro


class help:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if defer.check(cmd, 'jarvis', 'Secretary_Helen'):
            return
        msg.reply(
            "Command documentation: https://git.io/TARS.help. Start a "
            "command with .. to force me to respond."
        )


class status:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply(
            "{} · made by Croquembouche · Python {} · {} · alive for {}".format(
                acronym(),
                platform.python_version(),
                " ".join(
                    distro.linux_distribution(full_distribution_name=True)[:2]
                ),
                uptime(),
            )
        )


class github:
    """Provide links to the github"""

    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) > 0:
            if cmd.args['root'][0].startswith('i'):
                msg.reply("https://github.com/rossjrw/tars/issues")
            elif cmd.args['root'][0].startswith('p'):
                msg.reply("https://github.com/rossjrw/tars/pulls")
        else:
            msg.reply("https://github.com/rossjrw/tars")


class user:
    """Provide link to a user's Wikidot page"""

    @classmethod
    def command(cls, irc_c, msg, cmd):
        if defer.check(cmd, 'Secretary_Helen'):
            return
        if len(cmd.args['root']) > 0:
            msg.reply(
                "http://www.wikidot.com/user:info/{}".format(
                    "-".join(cmd.args['root'])
                )
            )
        else:
            raise CommandError("Specify a user's Wikidot username")


class tag:
    """Provide a link to a tag's page"""

    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) == 1:
            msg.reply(
                "http://www.scp-wiki.net/system:page-tags/tag/{}".format(
                    cmd.args['root'][0]
                )
            )
        elif len(cmd.args['root']) == 0:
            raise CommandError("Specify a tag")
        else:
            raise CommandError("Specify just one tag")
