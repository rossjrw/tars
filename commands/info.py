"""info.py

Commands that output basic information about the bot.
"""
class help:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("For usage instructions, see https://git.io/TARS.help")

class version:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("Made by Croquembouche")

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
