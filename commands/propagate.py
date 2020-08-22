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
                'fragment:scp-3939-64',
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
            msg.reply("Propagating all pages...")
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
        # 1. get a list of articles
        # 2. get data for each article
        # 2.5. put that data in the db
        pages = SCPWiki.get_all_pages()
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
            if index in breakpoints:
                reply("Propagated {} of {}".format(index, len(slugs)))
            prop_print("Updating {} in the database".format(slug))
            page = SCPWiki.get_one_page_meta(slug)
            DB.add_article(page, commit=False)
            if 'metadata' in page['tags']:
                metadata_slugs.append(slug)
                continue
        for slug in metadata_slugs:
            propagate.get_metadata(slug, reply=reply)
        DB.commit()

    @classmethod
    def get_metadata(cls, slug, **kwargs):
        """Handles metadata fetchers"""
        print("Getting metadata for {}".format(slug))
        reply = kwargs.get('reply', lambda x: None)
        # either attribution metadata or titles
        # we'll need the actual contents of the page
        reply("Getting metadata from {}".format(slug))
        html = SCPWiki.get_one_page_html(slug)
        soup = BeautifulSoup(html, "html.parser")
        if slug == 'attribution-metadata':
            return propagate.get_attribution_metadata(slug, soup, **kwargs)
        else:
            return propagate.get_series_metadata(slug, soup, **kwargs)

    @staticmethod
    def get_series_metadata(slug, soup, **kwargs):
        """Gets metadata for generic series pages that match assumptions"""
        reply = kwargs.get('reply', lambda x: None)
        # parse the html
        titles = soup.select(
            ".content-panel:nth-of-type(1) > ul:not(:first-of-type) li"
        )
        # <li><a href="/scp-xxx">SCP-xxx</a> - Title</li>
        for title in titles:
            # take the scp number from the URL, not the URL link
            # take the scp name from the text
            # if ANYTHING is unexpected, cancel and throw
            title = str(title)
            # sort out the scp-number
            pattern = re.compile(
                r"""
                <li>           # start of the "title"
                (.+?           # anything before the link
                href="/(.+?)"  # page slug
                >)(.+?)</a>    # page's literal title
                (?:            # start post-link group
                  .+?-\s?      # anything after link & before title
                  (.*?)        # page's meta title
                )?             # end post-link group; select if present
                </li>          # end of the "title"
            """,
                re.VERBOSE,
            )
            match = pattern.search(title)
            if not match:
                reply("Unknown link format: {}".format(title))
                continue
            # TODO if newpage in class then article does not exist
            if "class=\"newpage\"" in match.group(1):
                # article doesn't exist
                # DB.remove_article()
                continue
            num = match.group(2)
            meta_title = match.group(4)
            if meta_title in ("[ACCESS DENIED]", ""):
                meta_title = None
            if meta_title is None:
                if num.lower() != match.group(3).lower():
                    meta_title = match.group(3)
                    reply("Assuming title '{}' for {}".format(meta_title, num))
                else:
                    reply("{} has no title".format(num))
                    # don't add title but also don't delete
            # then add these numbers and names to the DB
            # if "<" in meta_title: print(num, meta_title)
            DB.add_article_title(num, num, meta_title, False)
        DB.commit()

    @staticmethod
    def get_attribution_metadata(slug, soup, **kwargs):
        """Gets attribution metadata"""
        reply = kwargs.get('reply', lambda x: None)
        # parse the html
        titles = soup.select(".wiki-content-table tr:not(:first-child)")
        # pages = dict of key slug and value actions[]
        pages = defaultdict(lambda: defaultdict(list))
        # actions to take for each type of metadata
        actions = {
            'author': lambda slug, values: DB.set_authors(
                slug, [v['name'] for v in values]
            ),
            'rewrite': lambda slug, values: None,
            'translator': lambda slug, values: None,
            'maintainer': lambda slug, values: None,
        }
        for title in titles:
            title = str(title)
            pattern = re.compile(
                r"""
                <tr>\s*
                <td>(.*?)</td>\s*  # affected page slug
                <td>(.*?)</td>\s*  # name
                <td>(.*?)</td>\s*  # metadata type
                <td>(.*?)</td>\s*  # date
                </tr>
            """,
                re.VERBOSE,
            )
            match = pattern.search(title)
            if not match:
                reply("Unknown attribute format: {}".format(title))
                continue
            pages[match.group(1)][match.group(3)].append(
                {'name': match.group(2), 'date': match.group(4)}
            )
        for slug, page in pages.items():
            if ':' in slug:
                # we don't store other categories
                continue
            for type_ in page:
                try:
                    actions[type_](slug, page[type_])
                except Exception as e:
                    reply(str(e))
        DB.commit()
