""" prop.py

For propagating the database with wiki data.
"""

import gevent

from helpers.api import SCPWiki
from helpers.error import CommandError
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer


def prop_print(text):
    """Prints with propagation identifier"""
    print("[{}] {}".format(nickColor("Propagation"), text))


def chunks(array, length):
    """Splits list into lists of given length"""
    for i in range(0, len(array), length):
        yield array[i : i + length]


class propagate:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # arg 1 should be a slug name
        if 'sample' in cmd:
            samples = [
                "scp-173",
                "scp-3939",
                "cone",
                "theme:ar",
                "scp-3790",  # should be a collab
            ]
            msg.reply("Adding sample data...")
            propagate.get_wiki_data_for_pages(samples, reply=msg.reply)
        elif 'all' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            propagate.get_wiki_data(reply=msg.reply)
        elif 'seconds' in cmd:
            propagate.get_wiki_data(
                reply=msg.reply, seconds=int(cmd['seconds'][0])
            )
        elif len(cmd.args['root']) > 0:
            propagate.get_wiki_data_for_pages(
                cmd.args['root'], reply=msg.reply
            )
        else:
            raise CommandError("Bad command")
        msg.reply("Done!")

    @classmethod
    def get_wiki_data(cls, **kwargs):
        """Gets wiki data for all pages."""
        reply = kwargs.pop('reply', lambda _: None)
        if 'seconds' in kwargs:
            reply(f"Getting wiki data for last{kwargs['seconds']} seconds")
        else:
            reply("Getting wiki data for all pages")
        pages_generator = SCPWiki.get_all_pages(**kwargs)
        for pages in pages_generator:
            for page in pages:
                if page['fullname'].startswith("fragment:"):
                    # Don't want to track fragments
                    continue
                DB.add_article(page, commit=False)
            # Give the API a moment to rest
            gevent.sleep(5)
        DB.commit()

    @classmethod
    def get_wiki_data_for_pages(cls, slugs, **kwargs):
        """Gets wiki data for the pages indicated by the list of slugs."""
        reply = kwargs.pop('reply', lambda _: None)
        reply(f"Gettings wiki data for {len(slugs)} specific pages")
        for slug in slugs:
            page = SCPWiki.get_one_page_meta(slug)
            DB.add_article(page, commit=False)
        DB.commit()
