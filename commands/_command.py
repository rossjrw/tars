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
        # argument list is currently in some sort of funky condensed state.
        # [mode,] type, nargs, name,...,name, docstring
        for arg in type(self).arguments:
            kwargs = {}
            # 1. Handle the mode, if present
            if isinstance(arg[0], str):
                mode = arg.pop(0)
                if mode == 'hidden':
                    kwargs['help'] = argparse.SUPPRESS
                else:
                    raise ValueError("Unknown mode: {}".format(mode))
            # 2. Handle the type
            if arg[0] is bool:
                assert arg[1] == 0, "bool nargs must be 0"
                kwargs['default'] = False
                kwargs['action'] = 'store_true'
            else:
                kwargs['type'] = arg[0]
                kwargs['nargs'] = arg[1]
                # ^ previous version has this set to * for validation later
            # 3. Handle the flags
            assert all([" " not in a for a in arg[2:-1]])
            # 4. Handle the docstring
            assert all([isinstance(a, str) for a in arg[2:]])
            if 'help' not in kwargs:
                kwargs['help'] = arg.pop(-1)
            parser.add_argument(*arg[2:], **kwargs)
        return parser
