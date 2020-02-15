"""showmore.py

Pick articles from a list.
Accesses the most recent list for the current channel from the db.
"""

from commands.search import search
from helpers.database import DB
from helpers.defer import defer
from helpers.error import CommandError, MyFaultError, isint

class showmore:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if(defer.check(cmd, 'jarvis', 'Secretary_Helen')): return
        if len(cmd.args['root']) > 1 or not all(map(isint, cmd.args['root'])):
            raise CommandError("Specify the number of the article you want "
                               "(or none to see the choices)")
        elif len(cmd.args['root']) == 0:
            number = 0
        else:
            number = int(cmd.args['root'][0])
        page_ids = DB.get_showmore_list(msg.raw_channel)
        if len(page_ids) == 0:
            raise MyFaultError("I have nothing to show more of.")
        if number > len(page_ids):
            raise MyFaultError("I only have {} results for the last search."
                               .format(len(page_ids)))
        pages = [DB.get_article_info(p_id) for p_id in page_ids]
        if number == 0:
            msg.reply("{} saved results (use ..sm to choose): {}".format(
                len(pages),
                " · ".join(["\x02{}\x0F {}".format(i + 1, p['title'])
                            for i, p in enumerate(pages[:10])])))
        else:
            msg.reply("{}/{} · {}".format(
                number, len(page_ids), search.parse_title(pages[number-1])))
