from helpers import parse

class colour:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not "root" in cmd.arguments:
            cmd.arguments["root"] = [msg.nick]
        reply = ""
        if len(cmd.arguments["root"]) > 0:
            for name in cmd.arguments['root']:
                reply += parse.nickColor(name)
        else:
            reply = "Malformed command"
        msg.reply(reply)
