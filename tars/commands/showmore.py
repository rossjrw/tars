"""showmore.py

Pick articles from a list.
Accesses the most recent list for the current channel from the db.
"""

import re
import pendulum as pd
from tars.helpers.database import DB
from tars.helpers.basecommand import Command
from tars.helpers.error import MyFaultError


class Showmore(Command):
    """Pick which article you want from previous search results.

    When TARS presents you with a list of articles to pick from, for example
    from the results of @command(search), use this command to pick which one
    you want to see.

    @example(..sm 2)(pick the 2nd article from the list.)

    Anyone can use @command(showmore) on the last list that TARS created in a
    given channel, even if TARS has been offline, and even if that person
    didn't issue the command that created that list. When a new list is created
    in a channel, it will overwrite the old list.

    Use @example(..sm) or @example(..sm 0) to see the whole list.

    Note that Secretary_Helen implements a similar command with a couple of
    differences:

    1. Picking a result will remove it from the list; for example, you can
    repeatedly issue @example(.sm 1) to iterate through the list. TARS does not
    remove results from the list; repeating issuing @example(.sm 1) will always
    get you the same article.
    2. Each user has their own list which other users cannot access. TARS
    stores list per-channel, so anyone in that channel can access them.
    """

    command_name = "showmore"
    defers_to = ["jarvis", "Secretary_Helen"]
    arguments = [
        dict(
            flags=['index'],
            type=int,
            nargs=None,
            default=0,
            help="""The index of the cached results list to fetch.

            If 0 or not provided, the whole list will be shown.
            """,
        )
    ]

    def execute(self, irc_c, msg, cmd):
        page_ids = DB.get_showmore_list(msg.raw_channel)
        if len(page_ids) == 0:
            raise MyFaultError("I have nothing to show more of.")
        if self['index'] > len(page_ids):
            raise MyFaultError(
                "I only have {} results for the last search.".format(
                    len(page_ids)
                )
            )
        pages = [DB.get_article_info(page_id) for page_id in page_ids]
        if self['index'] == 0:
            msg.reply(
                "{} saved results (use ..sm to choose): {}".format(
                    len(pages), Showmore.parse_multiple_titles(pages)
                )
            )
        else:
            msg.reply(
                "{}/{} · {}".format(
                    self['index'],
                    len(page_ids),
                    Showmore.parse_title(pages[self['index'] - 1]),
                )
            )

    @staticmethod
    def parse_title(page):
        """Makes a pretty string containing page info."""
        bold = "\x02{}\x0F"
        if Showmore.page_is_scp(page):
            if page['scp_num']:
                if page['title']:
                    title_preview = "{}: {}".format(
                        page['scp_num'].upper(), bold.format(page['title'])
                    )
                else:
                    title_preview = bold.format(page['scp_num'].upper())
            else:
                title_preview = bold.format(page['title'])
        else:
            title_preview = bold.format(page['title'])
        return "{} · {} · {} · {} · {}".format(
            title_preview,
            "by " + " & ".join(page['authors']),
            ("+" if page['rating'] >= 0 else "") + str(page['rating']),
            pd.from_timestamp(page['date_posted']).diff_for_humans(),
            "http://www.scp-wiki.wikidot.com/" + page['fullname'],
        )

    @staticmethod
    def parse_multiple_titles(pages):
        """Makes a pretty string representing a selection of pages."""
        return " · ".join(
            [
                "\x02{}\x0F {}".format(
                    i + 1,
                    p['title']
                    if not Showmore.page_is_scp(p)
                    else "{}: {}".format(p['scp_num'].upper(), p['title']),
                )
                for i, p in enumerate(pages[:10])
            ]
        )

    @staticmethod
    def page_is_scp(page):
        """Detects whether a given page is an SCP."""
        return any(
            # An SCP must have one of these conditions
            ['scp' in page['tags'], re.search(r"^scp-[0-9]{3,}", page['url'])]
        ) and not any(
            # An SCP cannot have any of these conditions
            [page['scp_num'] is None]
        )
