from helpers import parse

class colour:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not cmd.arguments["root"]:
            cmd.arguments["root"] = msg.nick
        if len(cmd.arguments["root"]) == 1:
            msg.reply(parse.nickColor(cmd.arguments["root"][0]))
        elif len(cmd.arguments["root"]) == 2:
            msg.reply(parse.nickColor(cmd.arguments["root"][0], cmd.arguments["root"][1]))
        else:
            msg.reply("Malformed command")
