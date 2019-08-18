"""admin.py

A bunch of commands for Controllers to use.
"""

from helpers.greetings import kill_bye
from helpers.error import CommandError
import os, sys
from helpers.api import SCPWiki
from helpers.database import DB
import git
from helpers.defer import defer
from commands.analytic import gib
import re

class kill:
    """Kills the bot"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        msg.reply(kill_bye())
        irc_c.RAW("QUIT See you on the other side")
        irc_c.client.die()

class join:
    """Joins a channel"""
    # Note that the INVITE event is in plugins/parsemessages.py
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        if len(cmd.args['root']) > 0 and cmd.args['root'][0][0] == '#':
            channel = cmd.args['root'][0]
            irc_c.JOIN(channel)
            msg.reply("Joining {}".format(channel))
            irc_c.PRIVMSG(channel, "Joining by request of {}".format(msg.nick))
            DB.join_channel(channel)
        else:
            msg.reply("You'll need to specify a valid channel.")

class leave:
    """Leaves the channel"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        if cmd.hasarg('message','m'):
            leavemsg = " ".join(cmd.getarg('message','m'))
        else:
            leavemsg = None
        if len(cmd.args['root']) > 0:
            channel = cmd.args['root'][0]
        else:
            channel = msg.raw_channel
        irc_c.PART(channel, message=leavemsg)
        DB.leave_channel(channel)

class reload:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # do nothing - this is handled by parsemessage
        pass

class reboot:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        # reboot the bot completely
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        msg.reply("Rebooting...")
        irc_c.RAW("QUIT Rebooting, will be back soon!")
        os.execl(sys.executable, sys.executable, *sys.argv)

class update:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        """Update from github"""
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        msg.reply("Updating...")
        try:
            g = git.cmd.Git(".")
            g.pull()
        except Exception as e:
            msg.reply("Update failed.")
            raise
        msg.reply("Update successful - now would be a good time to reboot.")

class say:
    """Make TARS say something"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["obfuscate o"])
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if len(cmd.args['root']) == 0:
            raise CommandError("Must specify a recipient and message")
        if len(cmd.args['root']) == 1:
            raise CommandError("Must specify a message")
        if cmd.args['root'][0][0] == '/' or cmd.args['root'][1][0] == '/':
            # This is an IRC command
            say.issue_raw(irc_c, msg, cmd)
        else:
            message = " ".join(cmd.args['root'][1:])
            if cmd.hasarg('obfuscate') and msg.channel is not None:
                members = DB.get_aliases(None)
                members = re.compile(r"\b" + r"\b|\b".join(members) + r"\b",
                                     flags=re.IGNORECASE)
                message = members.sub(gib.obfuscate, message)
            irc_c.PRIVMSG(cmd.args['root'][0], message)
            if not cmd.args['root'][0] == msg.channel:
                msg.reply("Saying that to {}".format(cmd.args['root'][0]))

    @staticmethod
    def issue_raw(irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if cmd.args['root'][1][0] == '/':
            cmd.args['root'].pop(0)
        msg.reply("Issuing that...")
        irc_c.RAW(" ".join(cmd.args['root'][1:]))


class config:
    """Provide a link to the config page"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("http://scp-sandbox-3.wikidot.com/collab:tars")
        # TODO update this to final page (or src from .conf?)

class debug:
    """Random debug command, replaceable"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # msg.reply(", ".join("%s: %s" % item for item in vars(msg).items()))
        msg.reply(SCPWiki.get_page_id(['scp-3939']))
