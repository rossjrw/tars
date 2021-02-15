""" prop.py

For propagating the database with wiki data.
"""

from collections import defaultdict
import re

from bs4 import BeautifulSoup
import numpy as np

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
                'scp-173',
                'scp-1111',
                'scp-3939',
                'cone',
                'scp-series',
                'listpages-magic-and-you',
                'scp-4205',
                'omega-k',
                'component:ar-theme',
            ]
            msg.reply("Adding sample data...")
            propagate.get_wiki_data_for(samples, reply=msg.reply)
        elif 'tales' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            msg.reply("Fetching all tales... this will take a few minutes.")
            tales = SCPWiki.get_all_pages(tags=['tale'])
            propagate.get_wiki_data_for(tales, reply=msg.reply)
        elif 'all' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            propagate.get_all_pages(reply=msg.reply)
        elif 'metadata' in cmd:
            metadata_slugs = SCPWiki.get_all_pages(tags=['metadata'])
            msg.reply("Propagating metadata...")
            for slug in metadata_slugs:
                propagate.get_metadata(slug, reply=msg.reply)
        elif len(cmd.args['root']) > 0:
            propagate.get_wiki_data_for(cmd.args['root'], reply=msg.reply)
        else:
            raise CommandError("Bad command")
        msg.reply("Done!")

    @classmethod
    def get_all_pages(cls, **kwargs):
        reply = kwargs.get('reply', lambda x: None)
        reply("Propagating all pages...")
        pages = SCPWiki.get_all_pages()
        propagate.get_wiki_data_for(pages, reply=reply)

    @classmethod
    def get_recent_pages(cls, **kwargs):
        reply = kwargs.get('reply', lambda x: None)
        reply("Propagating recent pages...")
        pages = SCPWiki.get_recent_pages(259200)
        propagate.get_wiki_data_for(pages, reply=reply)

    @classmethod
    def get_wiki_data_for(cls, slugs, **kwargs):
        print("Getting wiki data!")
        reply = kwargs.get('reply', lambda x: None)
        metadata_slugs = []
        # get the wiki data for this article
        # we're taking all of root, so slug is a list
        reply("{} pages to propagate".format(len(slugs)))
        breakpoints = np.floor(np.linspace(0, 1, num=11) * len(slugs))
        for index, slug in enumerate(slugs):
            if index in breakpoints and index > 100:
                reply("Propagated {} of {}".format(index, len(slugs)))
            try:
                page = SCPWiki.get_one_page_meta(slug)
            except KeyError:
                # Raised when the page does not exist, for example if it has
                # been deleted during propagation
                reply("{} does not exist".format(slug))
                DB.delete_article(slug)
                continue
            if slug.startswith("fragment:"):
                # Don't want to track fragments
                DB.delete_article(slug)
                continue
            DB.add_article(page, commit=False)
            if 'metadata' in page['tags']:
                metadata_slugs.append(slug)
                continue
        reply("Propagated {} of {}".format(len(slugs), len(slugs)))
        for slug in metadata_slugs:
            # The Crom API already has all the metadata attached, so there's no
            # need for TARS to handle it specifically
            # propagate.get_metadata(slug, reply=reply)
            pass
        DB.commit()
