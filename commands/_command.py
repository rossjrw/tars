"""
_command.py

Provides the base Command class that all commands inherit from.
"""

import argparse
import copy
import shlex

from helpers.error import ArgumentMessage, CommandError

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
        of that argument instead of its uppercase"""
        return action.dest

class Command:
    command_name = None
    arguments = []
    defers_to = []

    def __init__(self, message):
        self.args = None
        # This method is called for all commands when they are instantiated.
        # Commands must not define their own __init__.
        # message is a string representing the message arguments.
        # self.args will become the parsed Namespace object.
        parser = self.get_parser()
        message = message.replace("'", "<<APOS>>")
        message = message.replace('\\"', "<<QUOT>>") # explicit \"
        try:
            message = shlex.split(message, posix=False)
            # posix=False does not remove quotes
            message = [m.strip('"') for m in message]
        except ValueError:
            # raised if shlex detects fucked up quotemarks
            # message = message.split()
            raise CommandError("Unmatched quotemark. Use \\\" to escape a "
                               "literal quotemark.")
        message = [w.replace("<<APOS>>", "'") for w in message]
        message = [w.replace("<<QUOT>>", '"') for w in message]
        try:
            self.args = parser.parse_args(message)
        except ArgumentMessage as e:
            raise CommandError(str(e))

    def get_parser(self):
        """Returns the argument parser for this command."""
        parser = ArgumentParser(prog=type(self).command_name,
                                formatter_class=HelpFormatter)
        # arguments is a list of dicts
        # flags[], type, nargs, mode, help, choices
        for arg in copy.deepcopy(type(self).arguments):
            # 1. Handle the mode, if present
            if 'mode' in arg:
                mode = arg.pop('mode')
                if mode == 'hidden':
                    arg['help'] = argparse.SUPPRESS
                else:
                    raise ValueError("Unknown mode: {}".format(mode))
            # 2. Handle the type
            if arg['type'] is bool:
                if 'nargs' in arg and arg['nargs'] != 0:
                    raise ValueError("bool args must be 0 or not present")
                arg['default'] = False
                arg['action'] = 'store_true'
                arg.pop('type')
                arg.pop('nargs', None)
            # Other types are self-sufficient
            # 3. Handle the flags
            flags = arg.pop('flags')
            assert all([" " not in f for f in flags])
            assert all([isinstance(f, str) for f in flags])
            # 4. Handle the docstring
            if 'help' not in arg:
                raise ValueError("arg must have help string")
            parser.add_argument(*flags, **arg)
        # Add a hidden argument that takes the remainder of the command
        # these will be later added to the root argument
        parser.add_argument("_REMAINDER_",
                            nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        return parser

    def __contains__(self, arg):
        """Checks for argument presence via `in` operator"""
        return arg in self.args

    def __getitem__(self, arg):
        """Retrieves argument value via getitem operator"""
        return getattr(self.args, arg)
