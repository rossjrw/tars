""" prop.py

For propagating the database with wiki data.
"""

from helpers.api import SCPWiki
from helpers.error import CommandError
from pprint import pprint
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer
from bs4 import BeautifulSoup
import re

def prop_print(text):
    print("[{}] {}".format(nickColor("Propagation"), text))

def chunks(array, length):
    for i in range(0, len(array), length):
        yield array[i:i + length]

class propagate:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # arg 1 should be a url name
        if 'sample' in cmd:
            samples = ['scp-173','scp-1111','scp-3939','cone','scp-series',
                       'listpages-magic-and-you','scp-4205','omega-k',
                       'component:ar-theme','fragment:scp-3939-64']
            msg.reply("Adding sample data...")
            propagate.get_wiki_data_for(samples, reply=msg.reply)
        elif 'tales' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            msg.reply("Fetching all tales... this will take a few minutes.")
            tales = SCPWiki.select({'tags_all':['tale']})
            pprint(tales)
            propagate.get_wiki_data_for(tales, reply=msg.reply)
            return
        elif 'all' in cmd:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            msg.reply("Propagating all pages...")
            propagate.get_all_pages(reply=msg.reply)
            return
        elif 'metadata' in cmd:
            # meta_urls = ['attribution-metadata',
            #              'scp-series',
            #              'scp-series-2',
            #              'scp-series-3',
            #              'scp-series-4',
            #              'scp-series-5',
            #              'scp-series-6']
            meta_urls = ['scp-series-5']
            # XXX TODO replace with getting pages tagged "metadata"
            msg.reply("Propagating metadata...")
            for url in meta_urls:
                propagate.get_metadata(url, reply=msg.reply)
        elif len(cmd.args['root']) > 0:
            propagate.get_wiki_data_for(cmd.args['root'], reply=msg.reply)
            return
        else:
            raise CommandError("Bad command")

    @classmethod
    def get_all_pages(cls, **kwargs):
        reply = kwargs.get('reply', lambda x: None)
        # 1. get a list of articles
        # 2. get data for each article
        # 2.5. put that data in the db
        pages = SCPWiki.select({'categories': ["_default"]})
        reply("{} pages to propagate".format(len(pages)))
        propagate.get_wiki_data_for(pages, reply=reply)
        reply("Done!")

    @classmethod
    def get_wiki_data_for(cls, urls, **kwargs):
        print("Getting wiki data!")
        reply = kwargs.get('reply', lambda x: None)
        # get the wiki data for this article
        # we're taking all of root, so url is a list
        for urls in chunks(urls, 10):
            print(urls)
            articles = SCPWiki.get_meta({'pages': urls})
            for url,article in articles.items():
                prop_print("Updating {} in the database".format(url))
                DB.add_article(article, commit=False)
                if 'metadata' in article['tags']:
                    # TODO use list from above
                    pass # skip for now
                    propagate.get_metadata(url, reply=reply)
        reply("Done!")
        DB.commit()

    @classmethod
    def get_metadata(cls, url, **kwargs):
        print("Getting metadata for {}".format(url))
        reply = kwargs.get('reply', lambda x: None)
        # either attribution metadata or titles
        # we'll need the actual contents of the page
        reply("Getting metadata from {}".format(url))
        page = SCPWiki.get_page({'page': url})
        soup = BeautifulSoup(page['html'], "html.parser")
        # parse the html
        titles = soup.select(".content-panel:nth-of-type(1) > ul:not(:first-of-type) li")
        # <li><a href="/scp-xxx">SCP-xxx</a> - Title</li>
        for title in titles:
            # take the scp number from the URL, not the URL link
            # take the scp name from the text
            # if ANYTHING is unexpected, cancel and throw
            title = str(title)
            # sort out the scp-number
            match = re.search(r"/(scp-[0-9]{3,4})", link['href'])
            if not match:
                reply("Unknown link format: {}".format(link))
                # raise ValueError("Unknown link format: {}".format(link))
                continue
            num = match.groups(1)
            # if newpage in class then article does not exist
            text = "".join([str(t) for t in text])
            if text.startswith(" - "): text = text[3:]
            print(num, text)
            if len(text) == 0:
                reply("0-length title for {}".format(num))
                continue
            # then add these numbers and names to the DB
