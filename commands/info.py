"""info.py

Commands that output basic information about the bot.
"""

from datetime import timedelta
import time

import platform, distro

from helpers.config import CONFIG
from helpers.error import CommandError
from helpers.greetings import acronym
from helpers.defer import defer

start_time = time.time()


class help:
    @classmethod
    def execute(cls, irc_c, msg, cmd):
        if defer.check(cmd, 'jarvis', 'Secretary_Helen'):
            return
        msg.reply(
            "Command documentation: https://git.io/TARS.help. Start a "
            "command with .. to force me to respond."
        )


class status:
    @classmethod
    def execute(cls, irc_c, msg, cmd):
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


class github:
    """Provide links to the github"""

    @classmethod
    def execute(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) > 0:
            if cmd.args['root'][0].startswith('i'):
                msg.reply("{}/issues".format(CONFIG.repository))
            elif cmd.args['root'][0].startswith('p'):
                msg.reply("{}/pulls".format(CONFIG.repository))
        else:
            msg.reply(CONFIG.repository)


class user:
    """Provide link to a user's Wikidot page"""

    @classmethod
    def execute(cls, irc_c, msg, cmd):
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
    def execute(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) == 1:
            msg.reply(
                "http://www.scp-wiki.wikidot.com/system:page-tags/tag/{}".format(
                    cmd.args['root'][0]
                )
            )
        elif len(cmd.args['root']) == 0:
            raise CommandError("Specify a tag")
        else:
            raise CommandError("Specify just one tag")
