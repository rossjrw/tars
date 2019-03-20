from helpers.greetings import bad_command
class chevron:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if 'root' in cmd.args:
            # subtract 1 because ^ = no skips
            try:
                skip = int(cmd.args['root'][0]) - 1
            except ValueError:
                skip = 0
            try:
                limit = int(cmd.args['root'][1])
            except (IndexError, ValueError):
                limit = 10
            limit = 50 if limit > 50 else limit
            msg.reply("CHEVRON - skip {} - limit {}".format(skip, limit))
            # TODO database stuff
        else:
            msg.reply(bad_command(message="Missing arguments."))
