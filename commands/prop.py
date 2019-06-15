""" prop.py

For propagating the database with wiki data.
"""

from helpers.api import wikidot_api_key
from helpers.error import CommandError
from xmlrpc.client import ServerProxy
from pprint import pprint

class propagate:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if msg.nick != "Croquembouche":
            raise CommandError("Only Croquembouche can do that.")
        # arg 1 should be a url name
        if len(cmd.args['root']) > 0:
            propagate.get_wiki_data_for(cmd.args['root'])
        else:
            propagate.get_wiki_data()

    @classmethod
    def get_wiki_data(cls):
        # 1. get a list of articles
        # 2. get data for each article
        pass

    @classmethod
    def get_wiki_data_for(cls, url):
        # get the wiki data for this article
        pass
