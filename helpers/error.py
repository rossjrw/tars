"""error.py

Provide errors and things like that
"""


class CommandError(Exception):
    """Used for unresolvable errors found in user-submitted command syntax"""


class CommandNotExistError(Exception):
    """Used when a command does not exist"""


class MyFaultError(Exception):
    """Used for when a command succeeds but the output is failure"""


class ArgumentMessage(Exception):
    """Used for when argparse emits an error"""


def isint(integer):
    """Checks if something is an integer."""
    try:
        int(integer)
        return True
    except ValueError:
        return False


def nonelist(somelist):
    """Checks if something is a NoneList"""
    print(somelist)
    return (
        somelist is None
        or not isinstance(somelist, list)
        or len(somelist) == 0
        or all(i is None for i in somelist)
    )
