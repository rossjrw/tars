"""api.py

Provides methods for accessing API.

API keys should be kept in keys.secret.txt in the base directory. Lines must
be in pairs. The first line must contain the key name and nothing else. The
second line must contain the key value and nothing else. (Key names should only
be on odd lines, key values should only be on even lines.)

Valid key names are:
"""
possible_keys = ["irc_password", "wikidot_api", "google_cse_api",
                 "google_cse_id", "scuttle_api", "scuttle_oauth_id",
                 "scuttle_oauth_secret"]

import os.path
from xmlrpc.client import ServerProxy
import urllib3
from pprint import pprint

with open(os.path.dirname(__file__) + "/../keys.secret.txt") as file:
    si = iter(file.read().rstrip().splitlines())
    keylist = dict(zip(si, si))
    pprint(keylist)
    password = keylist['irc_password']
    wikidot_api_key = keylist['wikidot_api']
    google_api_key = keylist['google_cse_api']
    cse_key = keylist['google_cse_id']

class WikidotAPI:
    """Wrapper for Wikidot API functions."""
    def __init__(self, wikiname):
        self.w = wikiname
        self.s = ServerProxy('https://TARS:{}@www.wikidot.com/xml-rpc-api.php'
                             .format(wikidot_api_key))
    def select(self, selectors):
        """Equivalent to pages.select"""
        # TODO get site from config
        selectors['site'] = self.w
        return self.s.pages.select(selectors)
    def get_meta(self, selectors):
        """Equivalent to pages.get_meta. Limit 10 pages"""
        selectors['site'] = self.w
        return self.s.pages.get_meta(selectors)
    def select_files(self, selectors):
        """Equivalent to files.select. Limit 1 page"""
        selectors['site'] = self.w
        return self.s.files.select(selectors)
    def get_files_meta(self, selectors):
        """Equivalent to files.get_meta. Limit 10 files, 1 page"""
        selectors['site'] = self.w
        return self.s.files.get_meta(selectors)

SCPWiki = WikidotAPI("scp-wiki")
Sandbox3 = WikidotAPI("scp-sandbox-3")

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
