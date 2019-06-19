"""api.py

Provides methods for accessing API.

wikidot.secret.txt: Contains read-only Wikidot API key.
google.secret.txt: Contains Google CSE API key.
cse.secret.txt: Contains Custom Search Engine ID key.
"""

import os.path
from xmlrpc.client import ServerProxy
import urllib3

class WikidotAPI:
    """Wrapper for Wikidot API functions."""
    def __init__(self):
        self.s = ServerProxy('https://TARS:{}@www.wikidot.com/xml-rpc-api.php'
                             .format(wikidot_api_key))
    def select(self, selectors):
        """Equivalent to pages.select"""
        # TODO get site from config
        selectors['site'] = 'scp-wiki'
        return self.s.pages.select(selectors)
    def get_meta(self, selectors):
        """Equivalent to pages.get_meta"""
        selectors['site'] = 'scp-wiki'
        return self.s.pages.get_meta(selectors)

with open(os.path.dirname(__file__) + "/../wikidot.secret.txt") as file:
    wikidot_api_key = file.read().rstrip()
with open(os.path.dirname(__file__) + "/../google.secret.txt") as file:
    google_api_key = file.read().rstrip()
with open(os.path.dirname(__file__) + "/../cse.secret.txt") as file:
    cse_key = file.read().rstrip()
SCPWiki = WikidotAPI()
# TODO put all this stuff into WikidotAPI
http = urllib3.PoolManager()

def get_ups(article):
    r = http.request(
        'GET',
        "http://www.scp-wiki.net/ajax-module-connector.php",
        headers={
            'Cookie': "wikidot_udsession=1; {}; {};".format(cookie, token7),
            'Origin': "http://www.scp-wiki.net",
            'Referer': "http://www.scp-wiki.net/{}".format(article.url),
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "en-US,en;q=0.8",
            'User-Agent': "TARS",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Accept': "*/*",
            'X-Requested-With': "XMLHttpRequest",
            'Connection': "keep-alive"
        }
    )

def get_id(fullname):
    """Gets the Wikidot ID of a page."""
    pass
