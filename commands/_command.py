"""
_command.py

Provides the base Command class that all commands inherit from.
"""

import argparse
from helpers.error import ArgumentMessage

class ArgumentParser(argparse.ArgumentParser):
    """A new argparser that has all the custom stuff TARS needs."""
    def error(self, message):
        raise ArgumentMessage(message)
    def exit(self, status=0, message=None):
        if message is not None:
            raise ArgumentMessage(message)

class HelpFormatter(argparse.HelpFormatter):
    """A new --help formatter."""
    def _format_args(self, action, default_metavar):
        """Add an ellipsis to arguments that accept an unlimited number of
        arguments (all of them) instead of repeating the arg name over and
        over"""
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs is argparse.ZERO_OR_MORE:
            return "[{}...]".format(get_metavar(1)[0])
        if action.nargs is argparse.ONE_OR_MORE:
            return "{}...".format(get_metavar(1)[0])
        return super()._format_args(action, default_metavar)

    def _get_default_metavar_for_optional(self, action):
        """Change the default metavar for optional arguments to the long name
        of that argument""" # instead of what?
        return action.dest

class Command:
    command_name = None
    arguments = []
    defers_to = []
    def __init__(self):
        pass

    def get_parser(self):
        """Returns the argument parser for this command."""
        parser = ArgumentParser(prog=".{}".format(type(self).command_name),
                                formatter_class=HelpFormatter)
        # arguments is a list of dicts
        # flags[], type, nargs, mode, help, choices
        for arg in type(self).arguments:
            # 1. Handle the mode, if present
            if 'mode' in arg:
                if arg['mode'] == 'hidden':
                    arg['help'] = argparse.SUPPRESS
                else:
                    raise ValueError("Unknown mode: {}".format(arg['mode']))
            # 2. Handle the type
            if arg['type'] is bool:
                if 'nargs' in arg and arg['nargs'] != 0:
                    raise ValueError("bool args must be 0 or not present")
                arg['nargs'] = 0
                arg['default'] = False
                arg['action'] = 'store_true'
            # Other types are self-sufficient
            # 3. Handle the flags
            assert all([" " not in f for f in arg['flags']])
            assert all([isinstance(f, str) not in f for f in arg['flags']])
            # 4. Handle the docstring
            if 'help' not in arg:
                raise ValueError("arg must have help string")
            parser.add_argument(*arg['flags'], **arg)
        # Add a hidden argument that takes the remainder of the command
        # these will be later added to the root argument
        parser.add_argument("_REMAINDER_",
                            nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        return parser
