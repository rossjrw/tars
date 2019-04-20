"""admin.py

A bunch of commands for Controllers to use.
"""

from helpers.greetings import kill_bye

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
        if 'root' in cmd.args:
            irc_c.PART(cmd.args['root'][0], message=leavemsg)
        else:
            irc_c.PART(msg.raw_channel, message=leavemsg)

class reload:
    """Theoretically, reloads all plugins"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("Fuck off")
