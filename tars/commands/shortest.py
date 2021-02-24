""" shortest.py

For finding the shortest search term for a given article.

Used to be in analytic.py, but it's too long now.
"""

from itertools import product, combinations_with_replacement
from helpers.basecommand import Command
from helpers.database import DB
from helpers.error import CommandError, MyFaultError


class Shortest(Command):
    """Find the shortest search term for the page at URL, or the page named
    TITLE.

    Looks through the database and plays golf with article titles. Can be
    pretty slow, so give it a moment.

    Usually (but not always) returns two results: 'single string' and 'multi
    string'.

    TARS enables you to search for articles by a string that can contain
    spaces, using quotemarks, for example @example(.s "hello there") will
    search for an article whose title literally contains the string "hello
    there". The 'single string' result refers to this method.

    TARS can also search for articles by multiple strings, delimited by spaces,
    and this is also the only search method supported by other bots such as
    Secretary_Helen and Crom. The search @example(.s hello there) will search
    for an article whose titles contains both "hello" and "there" individually.
    The 'multi string' result refers to this method.

    If it takes TARS more than three minutes to calculate the shortest search
    for something, it will be kicked from IRC. If you find an article this
    happens for, please let me know.
    """

    command_name = ["shortest"]
    arguments = [
        dict(
            flags=['--url', '-u'],
            type=str,
            nargs=None,
            help="""The 'fullname' or 'slug' of an article as seen in its URL,
            e.g. 'scp-173'.""",
        ),
        dict(
            flags=['--title', '-t'],
            type=str,
            nargs=None,
            help="""An article's title. Doesn't have to be a real one.

            This argument can be any text, not just the title of an
            already-existing article. You can use this to see whether or not
            there will be an easy search for your article before you post it,
            which may help you avoid terrible titles like "Tower" or "Why?".
            """,
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        if 'title' not in self and 'url' not in self:
            raise CommandError(
                "At least one of --title or --url must be given."
            )
        if 'title' in self:
            title = self['title']
        elif 'url' in self:
            try:
                title = DB.get_article_info(
                    DB.get_articles(
                        [
                            {
                                'type': 'url',
                                # Handle case where the whole URL was entered
                                'term': self['url'][0].split("/")[-1],
                            }
                        ]
                    )[0]
                )['title']
            except IndexError as error:
                raise MyFaultError(
                    "I don't see any page at '{}'.".format(self['url'])
                ) from error
        pages = [
            DB.get_article_info(p_id)['title'] for p_id in DB.get_articles([])
        ]
        single_string = Shortest.get_substring(title, pages)
        helen_style = Shortest.get_multi_substring(title, pages)
        if single_string is None and helen_style is None:
            raise MyFaultError(
                "There's no unique search for \"{}\".".format(title)
            )
        msg.reply(
            "Shortest search for \"\x1d{}\x0F\" · {}".format(
                title, Shortest.pick_answer(single_string, helen_style),
            )
        )

    @staticmethod
    def pick_answer(single_string, helen_style):
        if single_string is None and helen_style is None:
            raise TypeError("None check should have been done by now")
        if helen_style is None or single_string == helen_style:
            if " " in single_string:
                # There are spaces, so display this in quotemarks, and better
                # be clear about what that means or people won't notice and
                # will be confused
                return (
                    "single-string: \"\x02{}\x0F\" · there is no unique "
                    "multi-string (Helen-compatible) search"
                ).format(single_string.lower())
            # No spaces, so is identical to a multi-string result anyway
            return "\x02{}\x0F".format(single_string.lower())
        if single_string is None:
            return "\x02{}\x0F".format(helen_style.lower())
        return "single string: \"\x02{}\x0F\" · multi string: \x02{}\x0F".format(
            single_string.lower(), helen_style.lower()
        )

    @staticmethod
    def get_term_sizes(max_length, term_count_limit):
        # terms is a list of lists
        # each sublist is a list of ints
        # each int is the length of the partial search term for this term
        # the result should be ordered by the total length of the search term
        # as a string (which means including whitespace)
        def whitelen(l):
            return sum(l) + len(l) - 1

        terms = []
        for count in range(1, term_count_limit + 1):
            terms.extend(
                combinations_with_replacement(range(max_length, 0, -1), count)
            )
        terms = sorted(terms, key=whitelen)
        return list(filter(lambda l: whitelen(l) <= max_length, terms))

    @staticmethod
    def get_all_substrings(selected_name, space_allowed=True):
        # returns a list of lists
        # each list is every possible substring of the given name at the given
        # length
        # the first returned list is empty, so the index of the returned master
        # list is synonymous with the length of each string in that list
        all_substrings = [[]]
        for length in range(1, len(selected_name) + 1):
            substrings = []
            # get name from start->length to (end-length)->end
            for offset in range(0, len(selected_name) - length + 1):
                substring = selected_name[offset : offset + length]
                if ' ' not in substring or space_allowed:
                    substrings.append(substring)
            all_substrings.append(substrings)
        return all_substrings

    @staticmethod
    def get_substring(selected_name, all_names):
        length_substrings = Shortest.get_all_substrings(selected_name)
        for substrings in length_substrings:
            for substring in substrings:
                if not any(
                    [
                        substring.lower() in name.lower()
                        for name in all_names
                        if name is not None and name != selected_name
                    ]
                ):
                    return substring
        return None

    @staticmethod
    def get_multi_substring(selected_name, all_names):
        all_names = [name for name in all_names if name is not None]
        # first: check if there are *any* unique matches
        if Shortest.count_matches(selected_name.split(), all_names) == 0:
            print("Returning early")
            return None
        # then check normally
        length_substrings = Shortest.get_all_substrings(selected_name, False)
        template_terms = Shortest.get_term_sizes(
            min(10, len(selected_name)), 4
        )
        already_searched_terms = []
        # iterate through each template term
        # need to replace each value in the template with a value from the
        # length_substrings
        for template_term in template_terms:
            # template_term = (4, 3, 2) or somesuch
            print(template_term)
            term_substring_lists = [
                length_substrings[l] for l in template_term
            ]
            search_terms = list(product(*term_substring_lists))
            for search_term in search_terms:
                if len(search_term) != len(set(search_term)):
                    continue
                if sorted(search_term) in already_searched_terms:
                    continue
                if Shortest.count_matches(search_term, all_names) == 1:
                    return " ".join(search_term)
                already_searched_terms.append(sorted(search_term))
        return None

    @staticmethod
    def count_matches(search_term, all_names):
        """Returns whether or not a search is a unique match.

        str full_search_term: The unparsed original search.
        list search_term: List of substrings to search for.
        list all_names: List of strings to search in.

        Returns enum matches:
            0 = search term does not appear
            1 = search term is unique
            2 = search term appears more than once
        """
        matches = 0
        for name in all_names:
            if all(term.lower() in name.lower() for term in search_term):
                matches += 1
                if matches > 1:
                    return 2
        if matches == 1:
            return 1
        return 0
