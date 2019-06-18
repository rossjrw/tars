""" prop.py

For propagating the database with wiki data.
"""

from helpers.api import Wikidot
from helpers.error import CommandError
from xmlrpc.client import ServerProxy
from pprint import pprint
from helpers.parse import nickColor

def prop_print(text):
    print("[{}] {}".format(nickColor("Propagation"), text))

class propagate:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # arg 1 should be a url name
        if cmd.hasarg('sample'):
            samples = ['scp-173','scp-1111','scp-3939','cone','scp-series',
                       'listpages-magic-and-you','scp-4205','omega-k',
                       'component:ar-theme','fragment:scp-3939-64']
            msg.reply("Adding sample data...")
            propagate.get_wiki_data_for(irc_c, samples, reply=msg.reply)
        elif cmd.hasarg('tales'):
            msg.reply("Fetching all tales...")
            tales = Wikidot.pages.select({'site':'scp-wiki', 'tags_all':['tale']})
            pprint(tales)
            propagate.get_wiki_data_for(irc_c, tales, reply=msg.reply)
        elif len(cmd.args['root']) > 0:
            propagate.get_wiki_data_for(irc_c, cmd.args['root'], reply = msg.reply)
        elif len(cmd.args) == 1:
            if msg.nick != "Croquembouche":
                raise CommandError(("Only Croquembouche can use this command"
                                    " without an argument."))
            propagate.get_wiki_data(irc_c, reply = msg.reply)
        else:
            raise CommandError("Bad command")

    @classmethod
    def get_wiki_data(cls, irc_c, **kwargs):
        reply = kwargs.get('reply', lambda x: None)
        # 1. get a list of articles
        # 2. get data for each article
        # 2.5. put that data in the db
        prop_print("Getting list of pages...")
        pages = Server.pages.select({'site': "scp-wiki",
                                     'categories': ["_default"]})
        prop_print("Found {} pages".format(len(pages)))
        reply("Done!")

    @classmethod
    def get_wiki_data_for(cls, irc_c, urls, **kwargs):
        print("Getting wiki data!")
        reply = kwargs.get('reply', lambda x: None)
        # get the wiki data for this article
        # we're taking all of root, so url is a list
        for urls in chunks(urls, 10):
            print(urls)
            articles = Wikidot.pages.get_meta({'site': "scp-wiki",
                                             'pages': urls})
            for url,article in articles.items():
                prop_print("Updating {} in the database".format(url))
                irc_c.db._driver.add_article(article)
        reply("Done!")

def chunks(array, length):
    for i in range(0, len(array), length):
        yield array[i:i + length]
