"""showmore.py

Pick articles from a list.
Accesses the most recent list for the current channel from the db.
"""

from helpers.defer import defer

class showmore:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if 'root' not in cmd.args:
            # 0 means "show everything"
            cmd.args['root'] = [0]
        else:
            try:
                # expect the argument to be a number
                cmd.args['root'][0] = int(cmd.args['root'][0])
            except ValueError:
                cmd.args['root'] = [0]
        number = cmd.args['root']
        if number == 0:
            msg.reply("Show more of what?")
        elif number > 10:
            msg.reply("Go fuck yourself.")
        else:
            for i in range(number):
                msg.reply("There's nothing to show!")
