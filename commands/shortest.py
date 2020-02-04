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
        if len(cmd.args['root']) < 1:
            raise CommandError("Specify a page's URL whose shortest search "
                               "term you want to find.")
        pages = [DB.get_article_info(
            p['id'])['title'] for p in DB.get_articles([], {})]
        try:
            title = DB.get_article_info(
                DB.get_articles(
                    [{'type': 'url', 'term': cmd.args['root'][0]}]
                )[0]['id'])['title']
        except IndexError:
            raise MyFaultError("I couldn't find the page with that URL.")
        single_string = shortest.get_substring(title, pages)
        helen_style = shortest.get_multi_substring(title, pages)
        if single_string is None and helen_style is None:
            raise MyFaultError("There's no unique search for {} (\"{}\")"
                               .format(cmd.args['root'][0], title))
        msg.reply("Shortest search for \x02{}\x0F · {}"
                  .format(cmd.args['root'][0],
                          shortest.pick_answer(single_string, helen_style)))

    @staticmethod
    def pick_answer(single_string, helen_style):
        if single_string is None and helen_style is None:
            raise TypeError("None check should have been done by now")
        if helen_style is None or single_string == helen_style:
            if ' ' in single_string:
                return "\"{}\"".format(single_string.lower())
            return single_string.lower()
        if single_string is None:
            return helen_style.lower()
        return "single string: \"{}\" · Helen-style: {}".format(
            single_string.lower(), helen_style.lower())

    @staticmethod
    def get_term_sizes(longest_term_length, term_count_limit):
        # terms is a list of lists
        # each sublist is a list of ints
        # each int is the length of the partial search term for this term
        # the result should be ordered by the total length of the search term
        # as a string (which means including whitespace)
        terms = []
        for count in range(1, term_count_limit+1):
            terms.extend(combinations_with_replacement(
                range(longest_term_length, 0, -1), count))
        return sorted(terms, key=lambda l: sum(l) + len(l) - 1)

    @staticmethod
    def get_all_substrings(selected_name, space_allowed=True):
        # returns a list of lists
        # each list is every possible substring of the given name at the given
        # length
        # the first returned list is empty, so the index of the returned master
        # list is synonymous with the length of each string in that list
        all_substrings = [[]]
        for length in range(1, len(selected_name)+1):
            substrings = []
            # get name from start->length to (end-length)->end
            for offset in range(0, len(selected_name)-length+1):
                substring = selected_name[offset:offset+length]
                if ' ' not in substring or space_allowed:
                    substrings.append(substring)
            all_substrings.append(substrings)
        return all_substrings

    @staticmethod
    def get_substring(selected_name, all_names):
        length_substrings = shortest.get_all_substrings(selected_name)
        for substrings in length_substrings:
            for substring in substrings:
                if not any([substring.lower() in name.lower()
                            for name in all_names
                            if name is not None
                            and name != selected_name]):
                    return substring
        return None

    @staticmethod
    def get_multi_substring(selected_name, all_names):
        length_substrings = shortest.get_all_substrings(selected_name, False)
        template_terms = shortest.get_term_sizes(min(3, len(selected_name)), 4)
        already_searched_terms = []
        # iterate through each template term
        # need to replace each value in the template with a value from the
        # length_substrings
        print("Template terms to evaluate:",len(template_terms))
        for template_term in template_terms:
            # template_term = (4, 3, 2) or somesuch
            term_substring_lists = [length_substrings[l] for l in template_term]
            search_terms = list(product(*term_substring_lists))
            print("Search terms:",len(search_terms),template_term)
            for search_term in search_terms:
                if len(search_term) != len(set(search_term)):
                    continue
                if sorted(search_term) in already_searched_terms:
                    continue
                if not any([all([term.lower() in name.lower()
                                 for term in search_term])
                            for name in all_names
                            if name is not None
                            and name != selected_name]):
                    return " ".join(search_term)
                already_searched_terms.append(sorted(search_term))
        return None
