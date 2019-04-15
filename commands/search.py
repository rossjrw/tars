"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.defer import defer
from helpers.api import api_key
from xmlrpc.client import ServerProxy
from helpers.error import CommandError
import re

date_offsets = {'s': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'W': 604800,
                'M': 2592000,
                'Y': 31557600
               }

class search:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # Check that we are actually able to do this
        # (might have to move to end for defer check)
        defer.check(irc_c, msg, "jarvis")
        # Parse the command itself
        cmd.expandargs(["tags t",
                        "author a",
                        "rating r",
                        "created c",
                        "category y",
                        "fullname f",
                        "regex x",
                        "random n d",
                        "summary s u",
                        "recommend rec m",
                        "ignorepromoted",
                       ])
        # Set the search mode of the input
        searchmode = 'normal'
        if cmd.hasarg('regex'):
            searchmode = 'regex'
        if cmd.hasarg('fullname'):
            searchmode = 'fullname'
        # Set the tags
        tags = {'include': [], 'exclude': []}
        if cmd.hasarg('tags'):
            for tag in cmd.getarg('tags'):
                if tag[0] == "-":
                    tags['exclude'].append(tag[1:])
                    continue
                if tag[0] == "+":
                    tags['include'].append(tag[1:])
                    continue
                tags['include'].append(tag)
        # Set the author
        authors = {'include': [], 'exclude': []}
        if cmd.hasarg('authors'):
            for author in cmd.getarg('authors'):
                if author[0] == "-":
                    authors['exclude'].append(author[1:])
                    continue
                if author[0] == "+":
                    authors['include'].append(author[1:])
                    continue
                authors['include'].append(author)
        # Set the rating
        # Cases to account for: modifiers, range, combination
        ratings = {'max': None, 'min': None}
        if cmd.hasarg('rating'):
            rating = cmd.getarg('rating')
            if ".." in rating:
                rating = rating.split("..")
                if len(rating) > 2:
                    raise CommandError("Too many ratings in range")
                try:
                    rating = [int(x) for x in rating]
                except ValueError:
                    raise CommandError("Ratings in a range must be whole"
                                       + " numbers")
                ratings['max'] = max(rating)
                ratings['min'] = min(rating)
            elif rating[0] in "><=":
                pattern = r"^(?P<comp>[<>=]{1,2})(?P<value>[0-9]+)"
                match = re.search(pattern, rating)
                if match:
                    try:
                        rating = int(match.group('value'))
                    except ValueError:
                        raise CommandError("Invalid rating comparison")
                    comp = match.group('comp')
                    if comp == ">=":
                        ratings['min'] = rating
                    elif comp == "<=":
                        ratings['max'] = rating
                    elif comp == "<":
                        ratings['max'] = rating - 1
                    elif comp == ">":
                        ratings['min'] = rating + 1
                    elif comp == "=":
                        ratings['min'] = rating
                        ratings['max'] = rating
                    else:
                        raise CommandError("Invalid rating comparison")
                else:
                    raise CommandError("Invalid rating comparison")
            else:
                try:
                    rating = int(rating)
                except ValueError:
                    raise CommandError("Rating must be a range, comparison"
                                       + " or number")
                ratings['max'] = rating
                ratings['min'] = rating
        # Set created date
        # Cases to handle: absolute, relative, range (which can be both)
        createds = {'max': None, 'min': None}
        if cmd.hasarg('created'):
            created = cmd.getarg('created').split("..")
            for key,date in enumerate(created):
                # Convert all dates to timestamps
                # 1. Relative
                pass
        # \/ Test stuff to be moved elsewhere after DB stuff
        print(api_key)
        s = ServerProxy('https://TARS:{}@www.wikidot.com/xml-rpc-api.php' \
                        .format(api_key))
        page = s.pages.get_meta({'site':'scp-wiki','pages':cmd.args['root']})
        print(page)
        for title,page in page.items():
            print(page)
            msg.reply(
                "{} | {} | {} | {}".format(
                    page['title'],
                    page['rating'],
                    "by " + page['created_by'],
                    page['created_at']
                )
            )

class regexsearch:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -x to true
        search.command(irc_c, msg, cmd)

class tags:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # TODO set -t to arguments
        search.command(irc_c, msg, cmd)
