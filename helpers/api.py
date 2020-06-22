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

    def get_one_page(self, slug):
        """Gets all SCUTTLE data for a single page."""
        return self.scuttle.page_by_slug(slug)

    def get_one_page_meta(self, slug):
        """Gets wikidot metadata for a single page."""
        return self.get_one_page(slug)['metadata']['wikidot_metadata']

    def get_one_page_html(self, slug):
        """Gets the HTML for a single page."""
        return self.get_one_page(slug)['latest_revision']

    def get_all_pages(self, *, tags=None, categories=None):
        """Gets a list of all slugs that satisfy the requirements."""
        if tags is None:
            tags = []
        assert isinstance(tags, list)
        if categories is None:
            categories = []
        else:
            raise NotImplementedError
        assert isinstance(categories, list)
        # get info for all pages
        if len(tags) == 1:
            slugs = [page['slug'] for page in self.scuttle.tag_pages(tags[0])]
        elif len(tags):
            raise NotImplementedError
        else:
            slugs = [page['slug'] for page in self.scuttle.all_pages()]
        return slugs

SCPWiki = ScuttleAPI("en")
