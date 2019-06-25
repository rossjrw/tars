"""showmore.py

Pick articles from a list.
Accesses the most recent list for the current channel from the db.
"""

from helpers.defer import defer
from helpers.error import isint

class showmore:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if len(cmd.args['root']) == 0:
            # 0 means "show everything"
            cmd.args['root'] = [0]
        if not isint(cmd.args['root'][0]):
            cmd.args['root'] = [0]
        number = cmd.args['root'][0]
        if number == 0:
            msg.reply("Show more of what?")
        elif number > 10:
            msg.reply("Go fuck yourself.")
        else:
            for i in range(number):
                msg.reply("There's nothing to show!")
