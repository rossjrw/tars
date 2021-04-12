"""parsing.py

Mixin to the base command that enables it to parse arguments.
"""

import argparse
import copy

from tars.helpers.basecommand.types import longstr
from tars.helpers.error import (
    CommandParsingError,
    CommandParsingHelp,
    MyFaultError,
)

# Sentinel value to indicate that an argument was not provided (e.g. for
# nargs="*", distinguishes between argument present but no parameters provided,
# and argument not present at all)
NoArgument = object()


class ParsingMixin:
    def get_parser(self):
        """Returns the argument parser for this command."""

        parser = ArgumentParser(
            prog=self._canonical_alias,
            description=type(self).__doc__,
            formatter_class=help_formatter,
        )
        # arguments is a list of dicts
        # flags[], type, nargs, mode, help, choices
        for arg in copy.deepcopy(type(self).arguments):
            # Check that actions have not been specified
            if 'action' in arg:
                raise TypeError("arguments may not specify an action")
            # Construct the action with a default permission level
            arg['action'] = self._make_argument_action(
                # 'false' is the permission level of Command
                # This should be the value of the lowest permission level
                # TODO Get this from the permission registry (when it exists)
                arg['type'],
                arg.pop('permission', False),
            )
            # Handle the mode, if present
            if 'mode' in arg:
                mode = arg.pop('mode')
                if mode == 'hidden':
                    arg['help'] = argparse.SUPPRESS
                else:
                    raise ValueError("Unknown mode: {}".format(mode))
            # Handle the nargs
            if 'nargs' not in arg and arg['type'] is not bool:
                arg['nargs'] = None
            # Assign sensible defaults
            if 'default' not in arg and arg['type'] is not bool:
                if arg['nargs'] in ['*', '+'] and arg['type'] is not longstr:
                    arg['default'] = []
                else:
                    # The default would usually be None
                    # Use __contains__ to check if argument is present
                    arg['default'] = NoArgument
                    # For '?', the `default` value is used if the option is
                    # not provided; if it is provided but with no argument,
                    # the value from `const` is taken, which defaults to
                    # None
            # Handle the type
            if arg['type'] is bool:
                if 'nargs' in arg and arg.pop('nargs') != 0:
                    raise ValueError("bool args must be 0 or not present")
                # The type has already been used to construct the Action, and
                # bool as a type is misleading otherwise, so ditch it
                arg.pop('type')
            # Handle the flags
            flags = arg.pop('flags')
            assert all([" " not in f for f in flags])
            assert all([isinstance(f, str) for f in flags])
            # Handle the docstring
            if 'help' not in arg:
                raise ValueError("arg must have help string")
            parser.add_argument(*flags, **arg)
        return parser

    def _make_argument_action(self, type, permission_level):
        """Constructs and returns an argparse action. The action first
        validates the arguments' usage against the permission checker and then
        stores the arguments into the namespace."""
        outer = self
        if type is bool:
            parent_action = argparse._StoreTrueAction
        else:
            parent_action = argparse._StoreAction

        class Action(parent_action):
            def __call__(self, parser, namespace, values, option_string=None):
                # Check this argument's permission against the context
                if not outer._permission_checker(permission_level):
                    raise MyFaultError(
                        "You don't have permission to use the {} "
                        "argument.".format(option_string)
                    )
                # Check if the values are longstr and if they are, concatenate
                if isinstance(values, (list, tuple)):
                    all_longstrs = [
                        isinstance(value, longstr) for value in values
                    ]
                    if all(all_longstrs):
                        values = " ".join(values)
                    elif any(all_longstrs):
                        raise TypeError(
                            "Not all longstrs for {}".format(option_string)
                        )
                # Bind the value
                super().__call__(parser, namespace, values, option_string)

        return Action


class ArgumentParser(argparse.ArgumentParser):
    """A new argparser that has all the custom stuff TARS needs."""

    def error(self, message):
        """Instead of crashing on error, reply a message"""
        raise CommandParsingError(message)

    def exit(self, _status=0, message=None):
        """Instead of crashing on error, reply a message"""
        if message is not None:
            raise CommandParsingError(message)

    def print_help(self, _file=None):
        """Reply with help instead of printing to console"""
        raise CommandParsingHelp(self.get_usage())

    def get_usage(self):
        """Gets the usage string for this command."""
        return self.format_usage()[7:]


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

    def _format_actions_usage(self, actions, groups):
        """Change the actions order to remove help and put positionals before
        optionals."""
        actions = [a for a in actions if "--help" not in a.option_strings]
        actions.sort(key=lambda action: action.option_strings != [])
        return super()._format_actions_usage(actions, groups)


def help_formatter(prog):
    """Override argparse's help formatter instantiation"""
    return HelpFormatter(
        prog, indent_increment=0, max_help_position=999, width=999
    )
