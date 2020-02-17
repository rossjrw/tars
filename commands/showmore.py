"""showmore.py

Pick articles from a list.
Accesses the most recent list for the current channel from the db.
"""

import re
import pendulum as pd
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
                len(pages), showmore.parse_multiple_titles(pages)))
        else:
            msg.reply("{}/{} · {}".format(
                number, len(page_ids), showmore.parse_title(pages[number-1])))

    @staticmethod
    def parse_title(page):
        """Makes a pretty string containing page info."""
        title_preview = "\x02{}\x0F"
        if showmore.page_is_scp(page):
            if page['scp_num']:
                title_preview = title_preview.format(page['scp_num'].upper())
                if page['title']:
                    title_preview += ": {}".format(page['title'])
            else:
                title_preview = title_preview.format(page['title'].upper())
        else:
            title_preview = title_preview.format(page['title'])
        return "{} · {} · {} · {} · {}".format(
            title_preview,
            "by " + " & ".join(page['authors']),
            ("+" if page['rating'] >= 0 else "") + str(page['rating']),
            pd.from_timestamp(page['date_posted']).diff_for_humans(),
            "http://www.scp-wiki.net/" + page['fullname'],
        )

    @staticmethod
    def parse_multiple_titles(pages):
        """Makes a pretty string representing a selection of pages."""
        return " · ".join(
            ["\x02{}\x0F {}".format(
                i + 1,
                p['title'] if not showmore.page_is_scp(p)
                else "{}: {}".format(p['scp_num'].upper(), p['title'])
            ) for i, p in enumerate(pages[:10])])

    @staticmethod
    def page_is_scp(page):
        """Detects whether a given page is an SCP."""
        return any(
            # An SCP must have one of these conditions
            ['scp' in page['tags'],
             re.search(r"^scp-[0-9]{3,}", page['url'])]
        ) and not any(
            # An SCP cannot have any of these conditions
            [page['scp_num'] is None]
        )
