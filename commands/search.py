"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from random import random

from commands import Command
from commands.gib import Gib
from commands.showmore import Showmore

from edtf import parse_edtf
from edtf.parser.edtf_exceptions import EDTFParseException
from fuzzywuzzy import fuzz
from googleapiclient.discovery import build
import pendulum as pd

from helpers.defer import defer
from helpers.api import GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
from helpers.error import CommandError, isint
from helpers.database import DB

try:
    import re2 as re
except ImportError:
    print("re2 failed to load, falling back to re")
    import re


class Search(Command):
    """Searches the wiki for pages.

    Provides URLs and basic info for the page(s) that match your search
    criteria. Searching is never case-sensitive.

    If TARS finds more than one article that matches your criteria (and if you
    didn't specify @argument(random), @argument(summary) or
    @argument(recommend)), it will provide a list of matches and ask if you
    meant any of them. To pick your article from the list, see
    @command(showmore).

    @command(regexsearch), @command(tags), @command(random) and
    @command(lastcreated) are aliases of this command.

    @example(TARS: search -t +scp +meta -r >100 -c 2014)(matches pages tagged
    both "scp" and "meta", with a rating of more than 100, posted in 2014.)

    @example(.s Insurgency --rating 20..80 --created 2018-06..2018)(matches
    pages that contain the word "Insurgency" in the title, which have a rating
    of between 20 and 80, and were created between June 1st 2018 and the end of
    2018.)

    @example(.s Unexplained Location -f -c 20d..40W3d --random)(matches pages
    whose name is exactly "Unexplained Location" created between 20 days and
    [40 weeks + 3 days] ago, and returns a random one.)

    @example(.s -x ^SCP-\d*2$ -m)(matches articles that start with "SCP-"
    followed by any amount of numbers so long as that number ends in a 2, and
    returns the one that most needs extra attention.)
    """

    command_name = "search"
    defers_to = ["jarvis", "Secretary_Helen"]
    arguments = [
        dict(
            flags=['title'],
            type=str,
            nargs='*',
            help="""Search for pages whose title contains all of these words.

            Words are space-separated. Like all commands, anything wrapped in
            quotemarks (`"`) will be treated as a single word. If you leave
            @argument(title) empty, then it will match all pages, and you'll
            need to specify more criteria. If you actually need to search for
            quotemarks, escape them with a backslash - e.g. `.s \\'The
            Administrator\\'`.""",
        ),
        dict(
            flags=['--regex', '-x'],
            type=str,
            nargs='+',
            help="""Filter pages by a regular expression.

            You may use more than one regex in a single search, still
            delimited by a space. If you want to include a literal space in
            the regex, you should either wrap the whole regex in quotes or use
            `\\s` instead.""",
        ),
        dict(
            flags=['--tags', '--tag', '--tagged', '-t'],
            type=str,
            nargs='+',
            help="""Filter pages by tags.

            The matched pages must have all the tags that you specified,
            unless that tag starts with `-`, in which case they must not
            have that tag.""",
        ),
        dict(
            flags=['--author', '--au', '--by', '-a'],
            type=str,
            nargs='+',
            help="""Filter pages by exact author name.

            The matched pages must have all the authors that you specified,
            unless that author starts with `-`, in which case they must not
            have that author.""",
        ),
        dict(
            flags=['--rating', '-r'],
            type=str,
            nargs='+',
            help="""Filter pages by rating.

            Prefix the number with any of `<`, `>`, `=`. Default is
            `>`. Can also specify a range of ratings with two dots, e.g.
            `20..50`. Ranges are always inclusive.""",
        ),
        dict(
            flags=['--created', '--date', '-c'],
            type=str,
            nargs='+',
            help="""Filter pages by date of creation. Accepts both absolute and
            relative dates.

            Absolute dates must be in ISO-8601 format (YYYY-MM-DD, YYYY-MM or
            YYYY). Relative dates must be a number followed by a letter to
            specify how many units of time ago; valid units are `s m h d w M
            y`. These units are not case-sensitive, **except for m/M!** Use `m`
            for minutes and `M` for Months.

            Can use the same prefixes as @argument(rating) (`>` = 'older
            than', `<` = 'younger than', `=` = exact match). `=` is the default
            prefix if not specified, though this is pretty much guaranteed to
            never match a relative date.

            Also supports ranges of dates with two dots e.g. `2018..2019`.
            Ranges are always inclusive, and you can mix relative dates and
            absolute dates.""",
        ),
        dict(
            flags=['--category', '--cat', '-y'],
            type=str,
            nargs='+',
            help="""Filter pages by Wikidot category.

            By default, all categories are searched. If you include this
            argument but don't specify any categories, TARS will only search
            '_default'.""",
        ),
        dict(
            flags=['--parent', '-p'],
            type=str,
            nargs=None,
            help="""Filter pages by their parent page's slug.

            The parent page's slug must be given exactly (e.g. `-p
            antimemetics-division-hub`). The entire parent tree will be
            checked - the page will be found even if it's a great-grandchild
            of the **--parent**.""",
        ),
        dict(
            flags=['--summary', '--summarise', '-u'],
            type=bool,
            help="""Summarise search results.

            Instead of providing a link to a single article, TARS will
            summarise all articles that match the search criteria.""",
        ),
        dict(
            flags=['--random', '--rand', '--ran', '-d'],
            type=bool,
            help="""If your search matches more than one article, return a
            random one.""",
        ),
        dict(
            flags=['--recommend', '--rec', '-m'],
            type=bool,
            help="""If your search matches more than one article, return the
            one that most needs attention.""",
        ),
        dict(
            flags=['--newest', '--new', '-n'],
            type=bool,
            help="""If your search matches more than one article, return the
            newest one.""",
        ),
        dict(
            flags=['--order', '-o'],
            type=str,
            nargs=None,
            choices=['random', 'recommend', 'recent', 'none', 'fuzzy'],
            default='fuzzy',
            help="""Returns the results in a certain order.""",
        ),
        dict(
            flags=['--offset', '-f'],
            type=int,
            nargs=None,
            default=0,
            help="""Remove this many results from the top of the list.""",
        ),
        dict(
            flags=['--limit', '-l'],
            type=int,
            nargs=None,
            help="""Limit the number of results.""",
        ),
        dict(
            flags=['--verbose', '-v'],
            type=bool,
            help="""State the search criteria that TARS thinks you want.""",
        ),
        dict(
            flags=['--ignorepromoted'],
            type=bool,
            mode='hidden',
            help="""Ignore articles that have been promoted.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        # check to see if there are any arguments
        if len(self) == 1 and len(self['title']) == 0:
            raise CommandError("Must specify at least one search term")
        # Set the return mode of the output
        selection = {
            'ignorepromoted': self['ignorepromoted'],
            'order': self['order'],
            'limit': self['limit'],
            'offset': self['offset'],
        }
        if self['random']:
            selection['order'] = 'random'
            selection['limit'] = 1
        if self['recommend']:
            selection['order'] = 'recommend'
            selection['limit'] = 1
        if self['newest']:
            selection['order'] = 'recent'
            selection['limit'] = 1
        # What are we searching for?
        searches = []
        strings = []
        if len(self['title']) > 0:
            strings = self['title']
            searches.extend([{'term': s, 'type': None} for s in strings])
        # Add any regexes
        regexes = []
        for regex in self['regex']:
            try:
                re.compile(regex)
            except re.error as e:
                raise CommandError(
                    "'{}' isn't a valid regular expression: {}".format(
                        regex, e
                    )
                )
            regexes.append(regex)
            # don't append compiled regex - SQL doesn't like that
        searches.extend([{'term': r, 'type': 'regex'} for r in regexes])
        # Set the tags
        tags = {'include': [], 'exclude': []}
        for tag in self['tags']:
            if tag[0] == "-":
                tags['exclude'].append(tag[1:])
                continue
            if tag[0] == "+":
                tags['include'].append(tag[1:])
                continue
            tags['include'].append(tag)
        searches.append({'term': tags, 'type': 'tags'})
        # Set the author
        authors = {'include': [], 'exclude': []}
        for author in self['author']:
            if author[0] == "-":
                authors['exclude'].append(author[1:])
                continue
            if author[0] == "+":
                authors['include'].append(author[1:])
                continue
            authors['include'].append(author)
        searches.append({'term': authors, 'type': 'author'})
        # Set the rating
        # Cases to account for: modifiers, range, combination
        ratings = MinMax()
        for rating in self['rating']:
            if ".." in rating:
                rating = rating.split("..")
                if len(rating) > 2:
                    raise CommandError("Too many ratings in range")
                try:
                    rating = [int(x) for x in rating]
                except ValueError:
                    raise CommandError("Ratings in a range must be ints")
                try:
                    ratings >= min(rating)
                    ratings <= max(rating)
                except MinMaxError as e:
                    raise CommandError(str(e).format("rating"))
            elif rating[0] in [">", "<", "="]:
                pattern = r"^(?P<comp>[<>=]{1,2})(?P<value>[0-9]+)"
                match = re.search(pattern, rating)
                if match:
                    try:
                        rating = int(match.group('value'))
                    except ValueError:
                        raise CommandError("Invalid rating comparison")
                    comp = match.group('comp')
                    try:
                        if comp == ">=":
                            ratings >= rating
                        elif comp == "<=":
                            ratings <= rating
                        elif comp == "<":
                            ratings < rating
                        elif comp == ">":
                            ratings > rating
                        elif comp == "=":
                            ratings >= rating
                            ratings <= rating
                        else:
                            raise CommandError("Unknown rating comparison")
                    except MinMaxError as e:
                        raise CommandError(str(e).format("rating"))
                else:
                    raise CommandError("Invalid rating comparison")
            else:
                try:
                    rating = int(rating)
                except ValueError:
                    raise CommandError(
                        "Rating must be a range, comparison, " "or number"
                    )
                # Assume =, assign both
                try:
                    ratings >= rating
                    ratings <= rating
                except MinMaxError as e:
                    raise CommandError(str(e).format("rating"))
        searches.append({'term': ratings, 'type': 'rating'})
        # Set created date
        # Cases to handle: absolute, relative, range (which can be both)
        createds = MinMax()
        created = self['created']
        # created is a list of date selectors - ranges, abs and rels
        # but ALL dates are ranges!
        created = [DateRange(c) for c in created]
        # created is now a list of DateRanges with min and max
        try:
            for selector in created:
                if selector.max is not None:
                    createds <= selector.max
                if selector.min is not None:
                    createds >= selector.min
        except MinMaxError as e:
            raise CommandError(str(e).format("date"))
        searches.append({'term': createds, 'type': 'date'})
        # Set category
        categories = {'include': [], 'exclude': []}
        for category in self['category']:
            if category[0] == "-":
                categories['exclude'].append(category[1:])
                continue
            if category[0] == "+":
                categories['include'].append(category[1:])
                continue
            categories['include'].append(category)
        searches.append({'term': categories, 'type': 'category'})
        # Set parent page
        parents = self['parent']
        if parents is not None:
            searches.append({'term': parents, 'type': 'parent'})
        # FINAL BIT - summarise commands
        if self['verbose']:
            verbose = "Searching for articles "
            if len(strings) > 0:
                verbose += "containing \"{}\"; ".format("\", \"".join(strings))
            if len(regexes) > 0:
                verbose += "matching the regex /{}/; ".format(
                    "/ & /".join(regexes)
                )
            if parents is not None:
                verbose += "whose parent page is '{}'; ".format(parents)
            if len(categories['include']) == 1:
                verbose += (
                    "in the category '" + categories['include'][0] + "'; "
                )
            elif len(categories['include']) > 1:
                verbose += (
                    "in the categories '" + "', '".join(categories) + "; "
                )
            if len(categories['exclude']) == 1:
                verbose += (
                    "not in the category '" + categories['exclude'][0] + "'; "
                )
            elif len(categories['exclude']) > 1:
                verbose += (
                    "not in the categories '" + "', '".join(categories) + "; "
                )
            if len(tags['include']) > 0:
                verbose += (
                    "with the tags '" + "', '".join(tags['include']) + "'; "
                )
            if len(tags['exclude']) > 0:
                verbose += (
                    "without the tags '" + "', '".join(tags['exclude']) + "'; "
                )
            if len(authors['include']) > 0:
                verbose += "by " + " & ".join(authors['include']) + "; "
            if len(authors['exclude']) > 0:
                verbose += "not by " + " or ".join(authors['exclude']) + "; "
            if ratings['max'] is not None and ratings['min'] is not None:
                if ratings['max'] == ratings['min']:
                    verbose += "with a rating of " + str(ratings['max']) + "; "
                else:
                    verbose += (
                        "with a rating between "
                        + str(ratings['min'])
                        + " and "
                        + str(ratings['max'])
                        + "; "
                    )
            elif ratings['max'] is not None:
                verbose += (
                    "with a rating less than " + str(ratings['max'] + 1) + "; "
                )
            elif ratings['min'] is not None:
                verbose += (
                    "with a rating greater than "
                    + str(ratings['min'] - 1)
                    + "; "
                )
            if createds['min'] is not None and createds['max'] is not None:
                verbose += (
                    "created between "
                    + createds['min'].to_datetime_string()
                    + " and "
                    + createds['max'].to_datetime_string()
                    + "; "
                )
            elif createds['max'] is not None:
                verbose += (
                    "created before "
                    + createds['max'].to_datetime_string()
                    + "; "
                )
            elif createds['min'] is not None:
                verbose += (
                    "created after "
                    + createds['min'].to_datetime_string()
                    + "; "
                )
            if verbose.endswith("; "):
                verbose = verbose[:-2]
            msg.reply(verbose)

        page_ids = DB.get_articles(searches)
        pages = [DB.get_article_info(p_id) for p_id in page_ids]
        pages = Search.order(pages, search_term=strings, **selection)

        if len(pages) >= 50:
            msg.reply(
                "{} results found - you're going to have to be more "
                "specific!".format(len(pages))
            )
            return
        if len(pages) > 3:
            msg.reply(
                "{} results (use ..sm to choose): {}".format(
                    len(pages), Showmore.parse_multiple_titles(pages)
                )
            )
            DB.set_showmore_list(msg.raw_channel, [p['id'] for p in pages])
            return
        if len(pages) == 0:
            # check if there's no args other than --verbose
            if len(self['title']) > 0:
                # google only takes 10 args
                url = google_search(
                    '"' + '" "'.join(self['title'][:10]) + '"', num=1
                )[0]
                if url is None:
                    msg.reply("No matches found.")
                    return
                if url['title'].endswith(" - SCP Foundation"):
                    url['title'] = url['title'][:-17]
                msg.reply(
                    "No matches found. Did you mean \x02{}\x0F? {}".format(
                        url['title'], url['link']
                    )
                )
            else:
                msg.reply("No matches found.")
            return
        for page in pages:
            msg.reply(
                Gib.obfuscate(
                    Showmore.parse_title(page),
                    DB.get_channel_members(msg.raw_channel),
                )
            )

    @staticmethod
    def order(
        pages,
        search_term=None,
        order=None,
        limit=None,
        offset=0,
        **wanted_filters,
    ):
        """Order the results of a search by `order`.
        If `order` is None, then order by fuzzywuzzy of the search term.
        `search_term` should be a list of strings.
        """
        # filters should only be {'ignorepromoted':False} atm
        filters = {
            'ignorepromoted': lambda page: not page['is_promoted'],
        }
        orders = {
            'random': lambda page: random(),
            'recent': lambda page: -page['date_posted'],
            'fuzzy': lambda page: -sum(
                [fuzz.ratio(s, page['title']) for s in search_term]
            ),
            # 'recommend': None,
        }
        for wanted_filter, wanted in wanted_filters.items():
            if not wanted:
                continue
            pages = filter(filters[wanted_filter], pages)
        if order is not None:
            pages = sorted(pages, key=orders[order])
        pages = pages[offset:]
        pages = pages[:limit]
        return pages


class Regexsearch(Search):
    """Searches the wiki for pages that match a regex. Exactly the same as
    @command(search), except your search terms are parsed as regular
    expressions. Not case-sensitive.

    @example(.rs ^SCP- -t -scp)(searches for articles starting with "SCP-" but
    that are not tagged 'scp'.)

    @example(.rs ^((?!the).)*$)(searches for articles that don't contain
    'the'.)
    """

    command_name = "regexsearch"
    arguments_prepend = "--regex"


class Tags(Search):
    """Search by tags. Equivalent to `.s -t [tag]`.
    """

    command_name = "tags"
    arguments_prepend = "--tags"


class Lastcreated(Search):
    """Generates a list of the 3 most recently created pages.

    @example(.lc -a Croquembouche)(shows the last 3 articles posted by
    Croquembouche.)
    """

    command_name = "lastcreated"
    arguments_prepend = "--order recent --limit 3"


class MinMax:
    """Stores a minimum int and a maximum int representing a range of values,
    inclusive.
    Once set, values are immutable.
    """

    def __repr__(self):
        return "MinMax({}..{})".format(self.min, self.max)

    def __init__(self, min_value=None, max_value=None):
        if max_value is not None and not isinstance(max_value, int):
            raise TypeError("Max must be int or None ({})".format(max_value))
        if min_value is not None and not isinstance(min_value, int):
            raise TypeError("Min must be int or None ({})".format(min_value))
        self.min = min_value
        self.max = min_value

    def __lt__(self, other):  # MinMax < 20
        if self.max is None:
            if self.min is not None and self.min > other:
                MinMax.throw('discrep')
            else:
                self.max = other - 1
        else:
            MinMax.throw('max')

    def __gt__(self, other):  # MinMax > 20
        if self.min is None:
            if self.max is not None and self.max < other:
                MinMax.throw('discrep')
            else:
                self.min = other + 1
        else:
            MinMax.throw('min')

    def __le__(self, other):  # MinMax <= 20
        if self.max is None:
            if self.min is not None and self.min > other:
                MinMax.throw('discrep')
            else:
                self.max = other
        else:
            MinMax.throw('max')

    def __ge__(self, other):  # MinMax <= 20
        if self.min is None:
            if self.max is not None and self.max < other:
                MinMax.throw('discrep')
            else:
                self.min = other
        else:
            MinMax.throw('min')

    def __getitem__(self, arg):  # MinMax['min']
        if arg == 'min':
            return self.min
        if arg == 'max':
            return self.max
        raise KeyError(arg + " not in a MinMax object")

    @staticmethod
    def throw(type):
        if type == 'discrep':
            raise MinMaxError("Minimum {0} cannot be greater than maximum {0}")
        if type == 'min':
            raise MinMaxError("Can only have one minimum {0}")
        if type == 'max':
            raise MinMaxError("Can only have one maximum {0}")
        raise ValueError("Unknown MinMaxError {}".format(type))


class MinMaxError(Exception):
    pass


class DateRange:
    """A non-precise date for creating date ranges"""

    def __repr__(self):
        return "DateRange({}..{})".format(self.min, self.max)

    # Each DateRange should have 2 datetimes:
    # 1. when it starts
    # 2. when it ends
    # Then when we make a range with the date, we take the one that gives the
    # largest range
    # Takes BOTH explicit ranges and implicit dates
    datestr = "{}-{}-{} {}:{}:{}"

    def __init__(self, input_date):
        self.input = input_date
        self.min = None
        self.max = None
        self.compare = "="
        # possible values:
        # 1. absolute date
        # 2. relative date
        # 3. range (relative or absolute)
        # for absolute:
        # parse
        # create max and min
        # for relative:
        # create a timedelta
        # subtract that from now
        # no need for max and min, subtraction is precise
        # for range:
        # create a DateRange for each
        # select max and min from both to create largest possible range
        # first let's handle the range
        if ".." in self.input:
            self.input = self.input.split("..")
            if len(self.input) != 2:
                raise CommandError("Date ranges must have 2 dates")
            # if the date is a manual range, convert to a DateRange
            self.max = []
            self.min = []
            for date in self.input:
                date = DateRange(date)
                self.max.append(date.max)
                self.min.append(date.min)
            # max and min are now both lists of possible dates
            # pick max and min to yield the biggest date
            # max: None is always Now
            # min: None is alwyas The Beginning of Time
            # for 2 absolute dates this is easy, just pick biggest diff
            # for 2 relative dates, pick both of whichever is not None
            # for 1:1, pick not None of relative then ->largest of absolute
            # filter None from lists
            self.max = [i for i in self.max if i]
            self.min = [i for i in self.min if i]
            # special case for 2 relative dates - both will only have max
            if len(self.max) == 2 and len(self.min) == 0:
                self.min = min(self.max)
                self.max = max(self.max)
                return
            diffs = []
            for i, minimum in enumerate(self.min):
                for j, maximum in enumerate(self.max):
                    diffs.append(
                        {
                            'i': i,
                            'j': j,
                            'diff': self.min[i].diff(self.max[j]).in_seconds(),
                        }
                    )
            diffs = max(diffs, key=lambda x: x['diff'])
            self.max = self.max[diffs['j']]
            self.min = self.min[diffs['i']]
            # do other stuff
            return
        # strip the comparison
        match = re.match(r"([>=<]{1,2})(.*)", self.input)
        if match:
            self.compare = match.group(1)
            self.input = match.group(2)
        if self.date_is_absolute():
            # the date is absolute
            # minimise the date
            minimum = pd.datetime(*self.date.lower_strict()[:6])
            minimum = minimum.set(hour=0, minute=0, second=0)
            # maximise the date
            maximum = pd.datetime(*self.date.upper_strict()[:6])
            maximum = maximum.set(hour=23, minute=59, second=59)
            if self.compare == "<":
                self.max = minimum
            elif self.compare == "<=":
                self.max = maximum
            elif self.compare == ">":
                self.min = maximum
            elif self.compare == ">=":
                self.min = minimum
            elif self.compare == "=":
                # = means between maximum and minimum
                self.min = minimum
                self.max = maximum
            else:
                raise CommandError(
                    "Unknown operator in absolute date "
                    "comparison ({})".format(self.compare)
                )
        elif re.match(r"([0-9]+[A-Za-z])+$", self.input):
            # the date is relative
            sel = [i for i in re.split(r"([0-9]+)", self.input) if i]
            # sel is now a number-letter-repeat list
            # convert list to dict via pairwise
            sel = DateRange.reverse_pairwise(sel)
            # convert all numbers to int
            sel = dict([a, int(x)] for a, x in sel.items())
            self.date = pd.now()
            # check time units
            for key in sel:
                if key not in 'smhdwMy':
                    raise CommandError(
                        "'{}' isn't a valid unit of time in a relative date. "
                        "Valid units are s, m, h, d, w, M, and y.".format(key)
                    )
            self.date = pd.now().subtract(
                years=sel.get('y', 0),
                months=sel.get('M', 0),
                weeks=sel.get('w', 0),
                days=sel.get('d', 0),
                hours=sel.get('h', 0),
                minutes=sel.get('m', 0),
                seconds=sel.get('s', 0),
            )
            if self.compare in ["<", "<="]:
                self.min = self.date
            elif self.compare in [">", ">="]:
                self.max = self.date
            elif self.compare == "=":
                self.max = self.date
                self.min = self.date
                # possible broken - may match to the second
            else:
                raise CommandError(
                    "Unknown operator in relative date "
                    "comparison ({})".format(self.compare)
                )
        else:
            raise CommandError(
                "'{}' isn't a valid absolute or relative date "
                "type".format(self.input)
            )

    def date_is_absolute(self):
        try:
            self.date = parse_edtf(self.input)
        except EDTFParseException:
            try:
                pd.parse(self.input)
            except pd.parsing.exceptions.ParserError:
                return False
            else:
                raise CommandError(
                    "Absolute dates must be of the format "
                    "YYYY, YYYY-MM or YYYY-MM-DD"
                )
        else:
            return True

    @staticmethod
    def reverse_pairwise(iterable):
        return dict(zip(*[iter(reversed(iterable))] * 2))

    def __getitem__(self, arg):  # MinMax['min']
        if arg is 'min':
            return self.min
        elif arg is 'max':
            return self.max
        else:
            raise KeyError(arg + " not in a DateRange object")


# TODO move this to helpers/api.py
def google_search(search_term, **kwargs):
    """Performs a mismatch search via google"""
    service = build("customsearch", "v1", developerKey=GOOGLE_CSE_API_KEY)
    res = (
        service.cse().list(q=search_term, cx=GOOGLE_CSE_ID, **kwargs).execute()
    )
    if 'items' in res:
        return res['items']
    return [None]
