"""
_command.py

Provides the base Command class that all commands inherit from.
"""

import argparse
import copy
import shlex
import re

from helpers.error import (
    CommandParsingError,
    CommandError,
    CommandParsingHelp,
    CommandUsageMessage,
)


# Sentinel value to indicate that an argument was not provided
NoArgument = object()


def regex_type(validation_regex, validation_reason):
    """Generates an argument type for a string matching a regex expression."""

    def rtype(arg_value, pattern=re.compile(validation_regex)):
        if not pattern.match(arg_value):
            raise argparse.ArgumentTypeError(validation_reason)
        return arg_value

    return rtype


class ArgumentParser(argparse.ArgumentParser):
    """A new argparser that has all the custom stuff TARS needs."""

    def error(self, message):
        """Instead of crashing on error, reply a message"""
        raise CommandParsingError(message)

    def exit(self, status=0, message=None):
        """Instead of crashing on error, reply a message"""
        if message is not None:
            raise CommandParsingError(message)

    def print_help(self):
        """Reply with help instead of printing to console"""
        raise CommandParsingHelp(self.format_usage())

    def format_usage(self):
        formatter = self._get_formatter()
        formatter.add_usage(
            self.usage, self._actions, self._mutually_exclusive_groups, "",
        )
        return formatter.format_help()


class HelpFormatter(argparse.HelpFormatter):
    """A new --help formatter."""

    def _format_args(self, action, default_metavar):
        """Add an ellipsis to arguments that accept an unlimited number of
        arguments (all of them) instead of repeating the arg name over and
        over"""
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs is argparse.ZERO_OR_MORE:
            return "[{}[]]".format(get_metavar(1)[0])
        if action.nargs is argparse.ONE_OR_MORE:
            return "{}[]".format(get_metavar(1)[0])
        return super()._format_args(action, default_metavar)

    def _get_default_metavar_for_optional(self, action):
        """Change the default metavar for optional arguments to the long name
        of that argument instead of its uppercase"""
        return action.dest


def help_formatter(prog):
    """Override argparse's help formatter instantiation"""
    return HelpFormatter(prog, width=999)


class Command:
    # The canonical name of this command, lowercase
    command_name = None

    # List of arguments that can be passed to this command; argparse syntax
    arguments = []

    # The names of the bots that this command defers to
    defers_to = []

    # A string to prepend to the start of the arguments (useful for aliases)
    arguments_prepend = ""

    def __init__(self, message):
        self.args = None
        # This method is called for all commands when they are instantiated.
        # Commands must not define their own __init__.
        # message is a string representing the message arguments.
        # The message does not contain the command name.
        # self.args will become the parsed Namespace object.

        # For command aliases, add the prepend string
        message = "{} {}".format(self.arguments_prepend, message)

        parser = self.get_parser()

        message = message.replace("'", "<<APOS>>")
        message = message.replace('\\"', "<<QUOT>>")  # explicit \"
        try:
            message = shlex.split(message, posix=False)
            # posix=False does not remove quotes
            message = [m.strip('"') for m in message]
        except ValueError as e:
            # raised if shlex detects fucked up quotemarks
            # message = message.split()
            raise CommandError(
                "Unmatched quotemark. Use \\\" to escape a "
                "literal quotemark."
            ) from e
        message = [w.replace("<<APOS>>", "'") for w in message]
        message = [w.replace("<<QUOT>>", '"') for w in message]
        try:
            # Can throw ArgumentError
            self.args = parser.parse_intermixed_args(message)
        except CommandParsingError as e:
            raise CommandError(
                "{}. {}".format(
                    str(e),
                    "Use '..help' for full documentation."
                    if self.command_name == Command.command_name
                    else "Use '..help {}' for this command's documentation.".format(
                        self.command_name
                    ),
                )
            ) from e
        except CommandParsingHelp as e:
            raise CommandUsageMessage(
                "{}{}".format(
                    "{}".format(str(e)),
                    ""
                    if self.__doc__ is None
                    else " — {} {}".format(
                        self.__doc__.splitlines()[0],
                        "Use '..help' for full documentation."
                        if self.command_name == Command.command_name
                        else "Use '..help {}' for this command's documentation.".format(
                            self.command_name
                        ),
                    ),
                )
            ) from e

    def get_parser(self):
        """Returns the argument parser for this command."""

        parser = ArgumentParser(
            prog=type(self).command_name,
            description=type(self).__doc__,
            formatter_class=help_formatter,
        )
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
            # 5. Handle the nargs
            if 'nargs' in arg:
                # Assign sensible defaults
                if 'default' not in arg:
                    if arg['nargs'] in ['*', '+']:
                        arg['default'] = []
                    else:
                        # The default would usually be None
                        # Use __contains__ to check if argument is present
                        arg['default'] = NoArgument
                else:
                    if arg['nargs'] in ['*', '+']:
                        assert isinstance(arg['default'], list)
            parser.add_argument(*flags, **arg)
        return parser

    def __contains__(self, arg):
        """Checks for argument presence"""
        # All arguments should have a default value of some sort
        if arg not in self.args:
            raise AttributeError(
                "arg {} doesn't exist on {}".format(arg, self.args)
            )
        # If the value is the sentinel then the argument was not provided AND
        # there is no default
        if getattr(self.args, arg) is NoArgument:
            return False

        return True

    def __getitem__(self, arg):
        """Retrieves argument value via getitem operator"""
        # Cannot access item is the argument was either not provided or if it
        # has no default value
        if getattr(self.args, arg) is NoArgument:
            raise AttributeError(
                "tried to access an argument ({}) that either wasn't given "
                "or has no default value".format(arg)
            )
        # Return either the given value or the default value
        return getattr(self.args, arg)

    def __len__(self):
        """Get the number of arguments given to this command"""
        return len(vars(self.args))
