"""postcrawler.py

Gets all the posts from a thread with known Wikidot ID.

python3 postcrawler.py [id]
"""

import pathlib
import sys
from pprint import pprint

import tomlkit
from scuttle import scuttle  # pip install python-scuttle

# Store API key in toml file in table 'keys' and key name 'scuttle_api'
with open(pathlib.Path.cwd() / "keys.secret.toml") as keys:
    keys = tomlkit.parse(keys.read())['keys']

if __name__ == '__main__':
    id = sys.argv[1]
    wiki = scuttle('en', keys['scuttle_api'], 1)
    threads = wiki.forum_threads(36)
    try:
        thread = [
            thread for thread in threads if thread['wd_thread_id'] == id
        ][0]['id']
    except IndexError:
        print("No such thread exists.")
        sys.exit(1)
    posts = wiki.thread_posts(thread)
    pprint(posts)
