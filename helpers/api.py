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
import time

import tomlkit
import requests

from scuttle import scuttle

with open(pathlib.Path.cwd() / "keys.secret.toml") as keys:
    keys = tomlkit.parse(keys.read())['keys']

GOOGLE_CSE_API_KEY = keys['google_cse_api']
GOOGLE_CSE_ID = keys['google_cse_id']
NICKSERV_PASSWORD = keys['irc_password']


def toml_url(url):
    """Grab a TOML file from URL and return the parsed object"""
    response = requests.get(url)
    return tomlkit.parse(response.text)


class ScuttleAPI:
    """Wrapper for Wikidot API functions.

    get_one methods return detailed info for one item.
    get_all methods return a non-detailed list of all items.
    get_gen methods return a generator for detailed info of all items.
    """

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
        elif len(tags) != 0:
            raise NotImplementedError
        else:
            slugs = [page['slug'] for page in self.scuttle.pages()]
        return slugs

    def get_all_recent_pages(self, seconds):
        """Gets data for pages created in the last n seconds."""
        pages = self.scuttle.pages_since(int(time.time() - seconds))
        return [page['slug'] for page in pages]

    def get_all_forums(self):
        """Gets all forums."""
        return self.scuttle.forums()

    def get_one_thread(self, scuttle_thread_id):
        """Get one thread by SCUTTLE ID."""
        return self.scuttle.thread(scuttle_thread_id)

    def get_all_threads_in_forum(self, scuttle_forum_id):
        """Gets all threads in a forum."""
        return self.scuttle.forum_threads(scuttle_forum_id)

    def get_gen_threads_in_forum_since(self, scuttle_forum_id, since):
        """Gets all threads in a forum created since a timestamp.
        Returns the verbose generator with 100 threads per page."""
        return self.scuttle.verbose(
            self.scuttle.forum_threads_since,
            scuttle_forum_id,
            since,
            limit=100,
        )

    def get_all_posts_since(self, since):
        """Gets all posts in a thread created since a timestamp.
        Returns the non-verbose, unpaginated post list."""
        return self.scuttle.posts_since(since)

    def get_gen_posts_since(self, since):
        """Gets all posts in a thread created since a timestamp.
        Returns the verbose generator with 100 posts per page."""
        return self.scuttle.verbose(
            self.scuttle.posts_since, since, limit=100,
        )


SCPWiki = ScuttleAPI("en")
