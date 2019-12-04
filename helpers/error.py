"""error.py

Provide errors and things like that
"""

class CommandError(Exception):
    """Used for unresolvable errors found in user-submitted command syntax"""
    pass

class CommandNotExistError(Exception):
    """Used when a command does not exist"""
    pass

class MyFaultError(Exception):
    """Used for when a command succeeds but the output is failure"""
    pass

class ArgumentMessage(Exception):
    """Used for when argparse emits an error"""
    pass

def isint(i):
    """Checks if something is an integer."""
    try:
        int(i)
        return True
    except ValueError:
        return False
