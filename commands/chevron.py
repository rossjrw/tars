class chevron:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if 'root' in cmd.args:
            # subtract 1 because ^ = no skips
            skip = cmd.args['root'][0] - 1
            try:
                limit = cmd.args['root'][1]
            except IndexError:
                limit = 10
        msg.reply("CHEVRON - skip {} - limit {}".format(skip, limit))
        # TODO database stuff
