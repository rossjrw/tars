"""admin.py

A bunch of commands for Controllers to use.
"""

from helpers.greetings import kill_bye
from helpers.error import CommandError
import os, sys

class kill:
    """Kills the bot"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply(kill_bye())
        irc_c.client.die()

class join:
    """Joins a channel"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) > 0 and cmd.args['root'][0][0] == '#':
            irc_c.JOIN(cmd.args['root'][0])
            msg.reply("Joining {}".format(cmd.args['root'][0]))
            irc_c.PRIVMSG(cmd.args['root'][0],
                          "Joining by request of {}".format(msg.nick))
        else:
            msg.reply("You'll need to specify a valid channel.")

class leave:
    """Leaves the channel"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if cmd.hasarg('message','m'):
            leavemsg = " ".join(cmd.getarg('message','m'))
        else:
            leavemsg = None
        if len(cmd.args['root']) > 0:
            irc_c.PART(cmd.args['root'][0], message=leavemsg)
        else:
            irc_c.PART(msg.raw_channel, message=leavemsg)

class reload:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # do nothing - this is handled by parsemessage
        pass

class reboot:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # reboot the bot completely
        if msg.nick == 'Croquembouche':
            msg.reply("Rebooting...")
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            msg.reply("Only Croquembouche can do that.")

class say:
    """Make TARS say something"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) == 0:
            raise CommandError("Must specify a recipient and message")
        if len(cmd.args['root']) == 1:
            raise CommandError("Must specify a message")
        if cmd.args['root'][0].lower() not in [
            "#tars",
            "croquembouche",
            "rounderhouse",
            "cutegirl",
            "tsatpwtcotttadc",
            "jazstar",
        ]:
            raise CommandError("You can only .say to #tars occupants atm")
        if cmd.args['root'][0][0] == '/' or cmd.args['root'][1][0] == '/':
            # This is an IRC command
            say.issue_raw(irc_c, msg, cmd)
        else:
            irc_c.PRIVMSG(cmd.args['root'][0], " ".join(cmd.args['root'][1:]))
            msg.reply("Saying that to {}".format(cmd.args['root'][0]))

    @staticmethod
    def issue_raw(irc_c, msg, cmd):
        if msg.nick == "Croquembouche":
            if cmd.args['root'][1][0] == '/':
                cmd.args['root'].pop(0)
            msg.reply("Issuing that...")
            irc_c.RAW(" ".join(cmd.args['root'][1:]))
        else:
            raise CommandError("Only Croquembouche can do that.")

class config:
    """Provide a link to the config page"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("http://scp-sandbox-3.wikidot.com/collab:tars")
        # TODO update this to final page (or src from .conf?)
