import sys
from itertools import product, combinations_with_replacement

NAMES = ['john smith',
         'amelie jones',
         'mark williams',
         'amanda brown',
         'logan wilson',
         'rebecca taylor',
         'armaldo johnson',
         'perrianne white',
         'glomorthy martin',
         'andolandoman anderson']

def get_term_sizes(longest_term_length, term_count_limit):
    # terms is a list of lists
    # each sublist is a list of ints
    # each int is the length of the partial search term for this term
    # the result should be ordered by the total length of the search term as a
    # string (which means including whitespace)
    terms = []
    for count in range(1, term_count_limit+1):
        terms.extend(combinations_with_replacement(
            range(longest_term_length, 0, -1), count))
    return sorted(terms, key=lambda l: sum(l) + len(l) - 1)

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

def get_substring(selected_name, all_names):
    length_substrings = get_all_substrings(selected_name)
    for substrings in length_substrings:
        for substring in substrings:
            if not any([substring.lower() in name.lower() for name in all_names
                        if name != selected_name]):
                return substring
    return None

def get_substring_no_spaces(selected_name, all_names):
    length_substrings = get_all_substrings(selected_name, False)
    template_terms = get_term_sizes(min(4, len(selected_name)), 4)
    # iterate through each template term
    # need to replace each value in the template with a value from the
    # length_substrings - and need to do this for every combination of values
    for template_term in template_terms:
        # template_term = (4, 3, 2) or somesuch
        term_substring_lists = [length_substrings[l] for l in template_term]
        search_terms = product(*term_substring_lists)
        for search_term in search_terms:
            if len(search_term) != len(set(search_term)):
                continue
            if not any([all([term.lower() in name.lower()
                             for term in search_term])
                        for name in all_names if name != selected_name]):
                return " ".join(search_term)
    return None

def go():
    try:
        name = sys.argv[1]
    except IndexError:
        print("Specify a name")
        return
    substring = get_substring(name, NAMES)
    print("Shortest unique substring: {}".format(substring))
    substring = get_substring_no_spaces(name, NAMES)
    print("Shortest unique substring without spaces: {}".format(substring))

if __name__ == '__main__':
    go()
