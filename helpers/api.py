"""api.py

Provides methods for accessing API.

API keys should be kept in keys.secret.toml in the base directory. This is a
TOML file containing a single table named 'keys' containing each key with its
value as a string.

The keys are:
    irc_password: The bots' IRC NickServ password.
    google_cse_api: The API key for the mismatch search via Google CSE.
    google_cse_id: The ID of the Google CSE.
    scuttle_api: A Personal Access Token for SCUTTLE.
"""
import json
import pathlib

import tomlkit

from scuttle import scuttle

with open(pathlib.Path(__file__).parent / "keys.secret.toml") as keys:
    keys = tomlkit.parse(keys)['keys']

class ScuttleAPI:
    """Wrapper for Wikidot API functions."""
    def __init__(self, domain):
        self.scuttle = scuttle(domain, keys['scuttle_api'], 1)

    def get_meta(self, selectors):
        """Equivalent to pages.get_meta. Limit 10 pages"""
        selectors['site'] = self.w
        return self.s.pages.get_meta(selectors)

    def get_page(self, selectors):
        """Equivalent to pages.get_one. Limit 1 page"""
        selectors['site'] = self.w
        return self.s.pages.get_one(selectors)

    def save_page(self, selectors):
        """Equivalent to pages.save_one Limit 1 page"""
        selectors['site'] = self.w
        return self.s.pages.save_one(selectors)

    def get_all_pages(self, *, tags=None, categories=None):
        if tags is None:
            tags = []
        assert isinstance(tags, list)
        if categories is None:
            categories = []
        assert isinstance(categories, list)
        # get info for all pages
        all_pages = self.scuttle.all_pages()
        # list of dicts of id: scuttle id, slug, wd_page_id
        # to filter, will need to get info for all pages

SCPWiki = ScuttleAPI("en")
