"""types.py

Extra argument types for command argument values.
"""

import argparse
import re


def matches_regex(validation_regex, validation_reason):
    """Generates an argument type for a string matching a regex expression."""
    if not isinstance(validation_regex, re.Pattern):
        validation_regex = re.compile(validation_regex)

    def string_matches_regex_type(arg_value, pattern=validation_regex):
        if not pattern.match(arg_value):
            raise argparse.ArgumentTypeError(validation_reason)
        return arg_value

    string_matches_regex_type.__name__ = validation_reason
    return string_matches_regex_type


def regex_type(arg_value):
    """Checks whether an argument compiles to a valid regex and returns the
    compiled regex."""
    try:
        arg_value = re.compile(arg_value)
    except re.error as error:
        raise argparse.ArgumentTypeError(
            "'{}' isn't a valid regular expression: {}".format(
                arg_value, error
            )
        )
    return arg_value


class longstr(str):
    """Used in the parsing action to concatenate the given arguments into a
    single long string."""
