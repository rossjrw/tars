"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.defer import defer
from helpers.api import api_key
from helpers.error import CommandError
from xmlrpc.client import ServerProxy
import re
import timeago
import iso8601
from iso8601 import ParseError
from datetime import datetime, timezone

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
                        "parent p",
                        "fullname f",
                        "regex x",
                        "random n d",
                        "summary s u",
                        "recommend rec m",
                        "verbose v",
                        "ignorepromoted",
                       ])
        # What are we searching for?
        searches = []
        if len(cmd.args) == 1 and len(cmd.args['root']) == 0:
            raise CommandError("Must specify at least one search term")
        else:
            searches = cmd.args['root']
        # Set the search mode of the input
        searchmode = 'normal'
        if cmd.hasarg('regex'):
            searchmode = 'regex'
        if cmd.hasarg('fullname'):
            searchmode = 'fullname'
        # Set the tags
        tags = {'include': [], 'exclude': []}
        if cmd.hasarg('tags'):
            if len(cmd.getarg('tags')) == 0:
                raise CommandError(("When using the tag filter (--tag/-t), at "
                                    "least one tag must be specified"))
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
        if cmd.hasarg('author'):
            if len(cmd.getarg('author')) == 0:
                raise CommandError(("When using the author filter "
                                    "(--author/-a), at least one author must "
                                    "be specified"))
            for author in cmd.getarg('author'):
                if author[0] == "-":
                    authors['exclude'].append(author[1:])
                    continue
                if author[0] == "+":
                    authors['include'].append(author[1:])
                    continue
                authors['include'].append(author)
        # Set the rating
        # Cases to account for: modifiers, range, combination
        ratings = MinMax()
        if cmd.hasarg('rating'):
            if len(cmd.getarg('rating')) == 0:
                raise CommandError(("When using the rating filter "
                                    "(--rating/-r), at least one rating must "
                                    "be specified"))
            for rating in cmd.getarg('rating'):
                if ".." in rating:
                    rating = rating.split("..")
                    if len(rating) > 2:
                        raise CommandError("Too many ratings in range")
                    try:
                        rating = [int(x) for x in rating]
                    except ValueError:
                        raise CommandError(("Ratings in a range must be plain "
                                            "numbers"))
                    ratings >= min(rating)
                    ratings <= max(rating)
                elif rating[0] in "><=":
                    pattern = r"^(?P<comp>[<>=]{1,2})(?P<value>[0-9]+)"
                    match = re.search(pattern, rating)
                    if match:
                        try:
                            rating = int(match.group('value'))
                        except ValueError:
                            raise CommandError("Invalid rating comparison")
                        comp = match.group('comp')
                        try:
                            if comp == ">=": ratings >= rating
                            elif comp == "<=": ratings <= rating
                            elif comp == "<": ratings < rating
                            elif comp == ">": ratings > rating
                            elif comp == "=": ratings = rating
                            elif comp == ">=" or comp == "<=":
                                raise CommandError(("Rating comparisons do not "
                            "support 'greater than' or 'lesser than' operators"))
                            else:
                                raise CommandError(("Unknown operator in rating "
                                                    "comparison"))
                        except MinMaxError as e:
                            raise CommandError(str(e) + " rating")
                    else:
                        raise CommandError("Invalid rating comparison")
                else:
                    try:
                        rating = int(rating)
                    except ValueError:
                        raise CommandError(("Rating must be a range, "
                                            "comparison, or number"))
                    # Assume =, assign both
                    if ratings['max'] is None:
                        ratings['max'] = max(rating)
                    else:
                        raise CommandError("Can only have one maximum rating")
                    if ratings['min'] is None:
                        ratings['min'] = max(rating)
                    else:
                        raise CommandError("Can only have one minimum rating")
        # Set created date
        # Cases to handle: absolute, relative, range (which can be both)
        createds = {'max': None, 'min': None}
        if cmd.hasarg('created'):
            if len(cmd.getarg('created')) == 0:
                raise CommandError(("When using the date of creation filter "
                                    "(--created/-c), at least one date must "
                                    "be specified"))
            created = cmd.getarg('created').split("..")
            if len(created) > 2:
                raise CommandError("Date ranges must have 2 dates only")
            comp = ""
            for key,date in enumerate(created):
                # Convert all dates to timestamps
                # Need to save the >/</=
                if date[0] in "><=":
                    pass
                try:
                    date = iso8601.parse_date(date)
                    msg.reply("Using absolute date")
                except ParseError:
                    msg.reply("Using relative date")
                pass
        # FINAL BIT - summarise commands
        if cmd.hasarg('verbose'):
            verbose = "Searching for articles "
            if len(searches) > 0:
                verbose += ("containing " +
                            ", ".join(searches) +
                            "; ")
            if len(tags['include']) > 0:
                verbose += ("with the tags " +
                            ", ".join(tags['include']) +
                            "; ")
            if len(tags['exclude']) > 0:
                verbose += ("with the tags " +
                            ", ".join(tags['exclude']) +
                            "; ")
            if len(authors['include']) > 0:
                verbose += ("by " +
                            ", ".join(authors['include']) +
                            "; ")
            if len(authors['exclude']) > 0:
                verbose += ("not by " +
                            ", ".join(authors['exclude']) +
                            "; ")
            if ratings['max'] is not None and ratings['min'] is not None:
                verbose += ("with a rating between " +
                            ratings['max'] + " and " + ratings['min'] +
                           "; ")
            elif ratings['max'] is not None:
                verbose += ("with a rating less than " +
                            ratings['max'] +
                            "; ")
            elif ratings['min'] is not None:
                verbose += ("with a rating greater than " +
                            ratings['min'] +
                            "; ")
            msg.reply(verbose)
        # \/ Test stuff to be moved elsewhere after DB stuff
        s = ServerProxy('https://TARS:{}@www.wikidot.com/xml-rpc-api.php' \
                        .format(api_key))
        pages = s.pages.get_meta({
            'site': 'scp-wiki',
            'pages': cmd.args['root']
        })
        if len(pages) == 0:
            msg.reply("No matches found.")
            return
        for title,page in pages.items():
            msg.reply(
                "\x02{}\x0F · {} · {} · {} · {}".format(
                    (page['title'] if not 'scp' in page['tags']
                     else page['title'] + ": " + "(title goes here)"),
                    "by " + page['created_by'],
                    ("+" if page['rating'] >= 0 else "") + str(page['rating']),
                    timeago.format(
                        iso8601.parse_date(page['created_at']),
                        datetime.now(timezone.utc)
                    ),
                    "http://www.scp-wiki.net/" + page['fullname'],
                )
            )

class regexsearch:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.args['regex'] = []
        search.command(irc_c, msg, cmd)

class tags:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.args['tags'] = cmd.args['root']
        cmd.args['root'] = []
        search.command(irc_c, msg, cmd)

class MinMax:
    """A dictionary whose keys are only mutable if they are None"""
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = min

    def __lt__(self, other): # MinMax < 20
        if self.max == None:
            if self.min > other: MinMax.throw('discrep')
            else: self.max = other - 1
        else: MinMax.throw('max')

    def __gt__(self, other): # MinMax > 20
        if self.min == None:
            if self.max < other: MinMax.throw('discrep')
            else: self.min = other + 1
        else: MinMax.throw('min')

    def __lte__(self, other): # MinMax <= 20
        if self.max == None:
            if self.min > other: MinMax.throw('discrep')
            else: self.max = other
        else: MinMax.throw('max')

    def __gte__(self, other): # MinMax <= 20
        if self.min == None:
            if self.max < other: MinMax.throw('discrep')
            else: self.min = other
        else: MinMax.throw('min')

    def __getitem__(self, arg): # MinMax['min']
        if arg is 'min': return self.min
        elif arg is 'max': return self.max
        else: raise KeyError(arg + " not in a MinMax object")

    @staticmethod
    def throw(type):
        if type == 'discrep':
            raise MinMaxError("Minimum {} cannot be greater than maximum {}")
        else:
            # Do I look like I give a damn
            raise MinMaxError("Can only have one " + type + "imum {}")

class MinMaxError(Exception):
    pass
