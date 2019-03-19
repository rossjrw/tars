from helpers import parse

class colour:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not "root" in cmd.args:
            cmd.args["root"] = [msg.nick]
        reply = ""
        if len(cmd.args["root"]) > 0:
            for name in cmd.args['root']:
                reply += parse.nickColor(name)
        else:
            reply = "Malformed command"
        msg.reply(reply)
