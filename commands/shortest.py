""" shortest.py

For finding the shortest search term for a given article.

Used to be in analytic.py, but it's too long now.
"""

from itertools import product, combinations_with_replacement
from helpers.database import DB
from helpers.error import CommandError, MyFaultError


class shortest:
    """Get the shortest unique search term for a page"""

    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(
            ["url u", "title t",]
        )
        if 'title' not in cmd and 'url' not in cmd:
            raise CommandError(
                "Usage: ..shortest [--url URL | --title TITLE] — find the "
                "shortest search for the page at URL, or the page named TITLE."
            )
        if 'title' in cmd:
            title = " ".join(cmd['title'])
        if 'url' in cmd:
            url = cmd['url'][0].split("/")[-1]
            if len(url) < 1:
                raise CommandError(
                    "Usage: ..shortest --url URL — URL should be the fullname "
                    "as seen in an article's URL, e.g. 'scp-173'"
                )
            try:
                title = DB.get_article_info(
                    DB.get_articles([{'type': 'url', 'term': url}])[0]
                )['title']
            except IndexError:
                raise MyFaultError("I couldn't find the page with that URL.")
        pages = [
            DB.get_article_info(p_id)['title'] for p_id in DB.get_articles([])
        ]
        single_string = shortest.get_substring(title, pages)
        helen_style = shortest.get_multi_substring(title, pages)
        if single_string is None and helen_style is None:
            raise MyFaultError(
                "There's no unique search for \"{}\".".format(title)
            )
        msg.reply(
            "Shortest search for \"\x1d{}\x0F\" · {}".format(
                title, shortest.pick_answer(single_string, helen_style),
            )
        )

    @staticmethod
    def pick_answer(single_string, helen_style):
        if single_string is None and helen_style is None:
            raise TypeError("None check should have been done by now")
        if helen_style is None or single_string == helen_style:
            if ' ' in single_string:
                return "\"\x02{}\x0F\"".format(single_string.lower())
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
        length_substrings = shortest.get_all_substrings(selected_name)
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
        if shortest.count_matches(selected_name.split(), all_names) == 0:
            print("Returning early")
            return None
        # then check normally
        length_substrings = shortest.get_all_substrings(selected_name, False)
        template_terms = shortest.get_term_sizes(
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
                if shortest.count_matches(search_term, all_names) == 1:
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
