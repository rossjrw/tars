class help:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("For usage instructions, see https://git.io/TARShelp")
        msg.reply("For a quick list of commands, see https://git.io/TARSquick")

class version:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("Made by Croquembouche")
