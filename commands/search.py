"""search.py

Search commands that search the wiki for stuff.
Commands:
    search - base command
    regexsearch - search with -x
    tags - search with root params lumped into -t
"""

from helpers.defer import defer
from helpers.api import wikidot_api_key, google_api_key, cse_key
from helpers.error import CommandError
from xmlrpc.client import ServerProxy
import re2 as re
import pendulum
from edtf import parse_edtf
from edtf.parser.edtf_exceptions import EDTFParseException
from google import google

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
        # Set the search mode of the input
        searchmode = 'normal'
        if cmd.hasarg('regex'): searchmode = 'regex'
        elif cmd.hasarg('fullname'): searchmode = 'fullname'
        # Set the return mode of the output
        returnmode = 'normal'
        if cmd.hasarg('random'): returnmode = 'random'
        elif cmd.hasarg('summary'): returnmode = 'summary'
        elif cmd.hasarg('recommend'): returnmode = 'recommend'
        # What are we searching for?
        searches = []
        if len(cmd.args) == 1 and len(cmd.args['root']) == 0:
            raise CommandError("Must specify at least one search term")
        else:
            if searchmode == 'normal':
                searches = cmd.args['root']
            elif searchmode == 'fullname':
                searches = [" ".join(cmd.args['root'])]
            elif searchmode == 'regex':
                for search in cmd.args['root']:
                    searches.append(re.compile(search))
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
                    try:
                        ratings >= min(rating)
                        ratings <= max(rating)
                    except MinMaxError as e:
                        raise CommandError(str(e).format("rating"))
                elif rating[0] in [">","<","="]:
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
                            elif comp == "=":
                                ratings >= rating
                                ratings <= rating
                            elif comp == ">=" or comp == "<=":
                                raise CommandError(("Rating comparisons do not "
                            "support 'greater than' or 'lesser than' operators"))
                            else:
                                raise CommandError(("Unknown operator in rating "
                                                    "comparison"))
                        except MinMaxError as e:
                            raise CommandError(str(e).format("rating"))
                    else:
                        raise CommandError("Invalid rating comparison")
                else:
                    try:
                        rating = int(rating)
                    except ValueError:
                        raise CommandError(("Rating must be a range, "
                                            "comparison, or number"))
                    # Assume =, assign both
                    try:
                        ratings >= rating
                        ratings <= rating
                    except MinMaxError as e:
                        raise CommandError(str(e).format("rating"))
        # Set created date
        # Cases to handle: absolute, relative, range (which can be both)
        createds = MinMax()
        if cmd.hasarg('created'):
            if len(cmd.getarg('created')) == 0:
                raise CommandError(("When using the date of creation filter "
                                    "(--created/-c), at least one date must "
                                    "be specified"))
            created = cmd.getarg('created')
            # created is a list of date selectors - ranges, abs and rels
            # but ALL dates are ranges!
            for key,selector in enumerate(created):
                created[key] = DateRange(selector)
            # created is now a list of DateRanges with min and max
            try:
                for key,selector in enumerate(created):
                    if selector.max is not None:
                        createds <= selector.max
                    if selector.min is not None:
                        createds >= selector.min
            except MinMaxError as e:
                raise CommandError(str(e).format("date"))
        # Set category
        categories = {'include': [], 'exclude': []}
        if cmd.hasarg('category'):
            if len(cmd.getarg('category')) == 0:
                raise CommandError(("When using the category filter "
                                    "(--category/-y), at least one category "
                                    "must be specified"))
            for category in cmd.getarg('category'):
                if category[0] == "-":
                    categories['exclude'].append(category[1:])
                    continue
                if category[0] == "+":
                    categories['include'].append(category[1:])
                    continue
                categories['include'].append(category)
        # Set parent page
        parents = None
        if cmd.hasarg('parent'):
            if len(cmd.getarg('parent')) != 1:
                raise CommandError(("When using the parent page filter "
                                    "(--parent/-p), exactly one parent URL "
                                    "must be specified"))
            parents = cmd.getarg('parent')[0]
        # FINAL BIT - summarise commands
        if cmd.hasarg('verbose'):
            verbose = "Searching for articles "
            if len(searches) > 0:
                if searchmode == 'normal':
                    verbose += ("containing '" +
                                "', '".join(searches) +
                                "'; ")
                elif searchmode == 'regex':
                    verbose += ("matching the regex /" +
                                "/ & /".join([s.pattern for s in searches]) +
                                "/; ")
            if parents is not None:
                verbose += ("whose parent page is " +
                            parents +
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
                if ratings['max'] == ratings['min']:
                    verbose += ("with a rating of " +
                                str(ratings['max']) +
                               "; ")
                else:
                    verbose += ("with a rating between " +
                                str(ratings['max']) +
                                " and " +
                                str(ratings['min']) +
                               "; ")
            elif ratings['max'] is not None:
                verbose += ("with a rating less than " +
                            str(ratings['max']) +
                            "; ")
            elif ratings['min'] is not None:
                verbose += ("with a rating greater than " +
                            str(ratings['min']) +
                            "; ")
            if createds['min'] is not None and createds['max'] is not None:
                verbose += ("created between " +
                            createds['min'].to_datetime_string() +
                            " and " +
                            createds['max'].to_datetime_string() +
                            "; ")
            elif createds['max'] is not None:
                verbose += ("created before " +
                            createds['max'].to_datetime_string() +
                            "; ")
            elif createds['min'] is not None:
                verbose += ("created after " +
                            createds['min'].to_datetime_string() +
                            "; ")
            if verbose.endswith("; "):
                verbose = verbose[:-2]
            msg.reply(verbose)
        # \/ Test stuff to be moved elsewhere after DB stuff
        s = ServerProxy('https://TARS:{}@www.wikidot.com/xml-rpc-api.php' \
                        .format(wikidot_api_key))
        pages = s.pages.get_meta({
            'site': 'scp-wiki',
            'pages': cmd.args['root']
        })
        if len(pages) == 0:
            if len(cmd.args) == 1 and len(cmd.args['root']) != 0:
                url = google.search('site:scp-wiki.net "' +
                                    '" "'.join(cmd.args['root']) +
                                    '"', 1)[0]
                if url.name.endswith(" - SCP Foundation"):
                    url.name = url.name[:-17]
                msg.reply(("No matches found. Did you mean: "
                           "\x02{}\x0F? {}")
                           .format(url.name, url.link))
            msg.reply("No matches found.")
            return
        for title,page in pages.items():
            msg.reply(
                "\x02{}\x0F · {} · {} · {} · {}".format(
                    (page['title'] if not 'scp' in page['tags']
                     else page['title'] + ": " + "(title goes here)"),
                    "by " + page['created_by'],
                    ("+" if page['rating'] >= 0 else "") + str(page['rating']),
                    pendulum.parse(page['created_at']).diff_for_humans(),
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
    # this MIGHT work for datetime, let's see
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = min

    def __lt__(self, other): # MinMax < 20
        if self.max == None:
            if self.min != None and self.min > other: MinMax.throw('discrep')
            else: self.max = other - 1
        else: MinMax.throw('max')

    def __gt__(self, other): # MinMax > 20
        if self.min == None:
            if self.max != None and self.max < other: MinMax.throw('discrep')
            else: self.min = other + 1
        else: MinMax.throw('min')

    def __le__(self, other): # MinMax <= 20
        if self.max == None:
            if self.min != None and self.min > other: MinMax.throw('discrep')
            else: self.max = other
        else: MinMax.throw('max')

    def __ge__(self, other): # MinMax <= 20
        if self.min == None:
            if self.max != None and self.max < other: MinMax.throw('discrep')
            else: self.min = other
        else: MinMax.throw('min')

    def __getitem__(self, arg): # MinMax['min']
        if arg is 'min': return self.min
        elif arg is 'max': return self.max
        else: raise KeyError(arg + " not in a MinMax object")

    @staticmethod
    def throw(type):
        if type == 'discrep':
            raise MinMaxError("Minimum {0} cannot be greater than maximum {0}")
        else:
            # Do I look like I give a damn
            raise MinMaxError("Can only have one " + type + "imum {0}")

class MinMaxError(Exception):
    pass

class DateRange:
    """A non-precise date for creating date ranges"""
    # Each DateRange should have 2 datetimes:
        # 1. when it starts
        # 2. when it ends
    # Then when we make a range with the date, we take the one that gives the
    # largest range
    # Takes BOTH explicit ranges and implicit dates
    datestr = "{}-{}-{} {}:{}:{}"
    def __init__(self, date):
        self.input = date
        self.min = None
        self.max = None
        self.compare = None
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
            if len(self.input) is not 2:
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
            for i,minimum in enumerate(self.min):
                for j,maximum in enumerate(self.max):
                    diffs.append(
                        {'i': i, 'j': j,
                         'diff': self.min[i].diff(self.max[j]).in_seconds()}
                    )
            diffs = max(diffs, key=lambda x: x['diff'])
            self.max = self.max[diffs['j']]
            self.min = self.min[diffs['i']]
            # do other stuff
            return
        # strip the comparison
        match = re.match(r"([<>=]{1,2})(.*)", self.input)
        if match:
            self.compare = match.group(1)
            self.input = match.group(2)
        if self.date_is_absolute():
            # the date is absolute
            # minimise the date
            self.min = pendulum.datetime(*self.date.lower_strict()[:6])
            self.min = self.min.set(hour=0, minute=0, second=0)
            # maximise the date
            self.max = pendulum.datetime(*self.date.upper_strict()[:6])
            self.max = self.max.set(hour=23, minute=59, second=59)
            pass
        elif re.match(r"([0-9]+[A-Za-z])+$", self.input):
            # the date is relative
            sel = [i for i
                   in re.split(r"([0-9]+)", self.input)
                   if i]
                # sel is now a number-letter-repeat list
                # convert list to dict via pairwise
            sel = DateRange.reverse_pairwise(sel)
            # convert all numbers to int
            sel = dict([a, int(x)] for a, x in sel.items())
            self.date = pendulum.now()
            # check time units
            for key,value in sel.items():
                # make units not case sensitive
                if key != 'M':
                    sel[key.lower()] = sel.pop(key)
                if key not in 'smhdwMy':
                    raise CommandError(("{} isn't a valid unit of time in a "
                                        "relative date. Valid units are s, m, "
                                        "h, d, w, M, and y.")
                                       .format(key))
            self.date = pendulum.now().subtract(
                years=sel.get('y', 0),
                months=sel.get('M', 0),
                weeks=sel.get('w', 0),
                days=sel.get('d', 0),
                hours=sel.get('h', 0),
                minutes=sel.get('m', 0),
                seconds=sel.get('s', 0),
            )
            if self.compare in ["<","<="]:
                self.min = self.date
            elif self.compare in [">",">="] or self.compare is None:
                self.max = self.date
            elif self.compare == "=":
                self.max = self.date
                self.min = self.date
                # possible broken - may match to the second
            else:
                raise CommandError(("Unknown operator in relative date "
                                    "comparison"))
        else:
            raise CommandError(("'" + self.input + "' isn't a valid absolute "
                                "or relative date type"))

    def date_is_absolute(self):
        try:
            self.date = parse_edtf(self.input)
        except EDTFParseException:
            try:
                pendulum.parse(self.input)
            except pendulum.parsing.exceptions.ParserError:
                return False
            else:
                raise CommandError(("Absolute dates must be of the format "
                                    "YYYY, YYYY-MM or YYYY-MM-DD"))
        else:
            return True

    @staticmethod
    def reverse_pairwise(iterable):
        return dict(zip(*[iter(reversed(iterable))]*2))

    def __getitem__(self, arg): # MinMax['min']
        if arg is 'min': return self.min
        elif arg is 'max': return self.max
        else: raise KeyError(arg + " not in a DateRange object")
