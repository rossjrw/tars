"""
Provides the base Command class that all commands inherit from.
"""

from abc import ABC, abstractmethod
import argparse
import copy
import shlex
import re

import tars.commands
from tars.helpers.error import (
    CommandParsingError,
    CommandError,
    CommandParsingHelp,
    CommandUsageMessage,
    MyFaultError,
)


# Sentinel value to indicate that an argument was not provided (e.g. for
# nargs="*", distinguishes between argument present but no parameters provided,
# and argument not present at all)
NoArgument = object()


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


def help_formatter(prog):
    """Override argparse's help formatter instantiation"""
    return HelpFormatter(
        prog, indent_increment=0, max_help_position=999, width=999
    )


class Command(ABC):
    """Base command extended by all commands that generates documentation from
    its internal argparse object. If this text appears outside of TARS' source
    code, something has gone wrong."""

    # The name of this command as it will appear in documentation
    command_name = None

    # The aliases that can be used to call this command
    aliases = []

    # The permission level required to call this command
    permission = False

    # List of arguments that can be passed to this command; argparse syntax
    arguments = []

    # A string to prepend to the start of the arguments (useful for aliases)
    arguments_prepend = ""

    def __init__(self, permission_checker):
        self.args = None
        # All commands must be registered
        if (
            self.__class__.__name__
            not in tars.commands.COMMANDS_REGISTRY.list_all_commands()
        ):
            raise ValueError(
                "command {} is not registered".format(self.__class__.__name__)
            )
        if len(self.aliases) == 0:
            raise ValueError(
                "command {} has no aliases".format(self.__class__.__name__)
            )
        self._canonical_alias = self.aliases[0]
        # Verify that the permission checker is a function
        if not callable(permission_checker):
            raise TypeError("permission_checker must be callable")
        self._permission_checker = permission_checker
        # Now check that the executor has permission to use the command
        if not self._permission_checker(self.permission):
            raise MyFaultError(
                "You don't have permission to use ..{}".format(
                    self._canonical_alias
                )
            )

    def _make_argument_action(self, type, permission_level):
        """Constructs and returns an argparse action. The action first
        validates the arguments' usage against the permission checker and then
        stores the arguments into the namespace."""
        outer = self
        if type is bool:
            ParentAction = argparse._StoreTrueAction
        else:
            ParentAction = argparse._StoreAction

        class Action(ParentAction):
            def __call__(self, parser, namespace, values, option_string=None):
                # Check this argument's permission against the context
                if not outer._permission_checker(permission_level):
                    raise MyFaultError(
                        "You don't have permission to use the {} "
                        "argument.".format(option_string)
                    )
                super().__call__(parser, namespace, values, option_string)

        return Action

    def parse(self, message):
        """Parses a command message to command arguments."""
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
                    if self.command_name is None
                    else "Use '..help {}' for this command's documentation.".format(
                        self._canonical_alias
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
                        if self.command_name is None
                        else "Use '..help {}' for this command's documentation.".format(
                            self._canonical_alias
                        ),
                    ),
                )
            ) from e

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
                arg['type'], arg.pop('permission', Command.permission)
            )
            # Handle the mode, if present
            if 'mode' in arg:
                mode = arg.pop('mode')
                if mode == 'hidden':
                    arg['help'] = argparse.SUPPRESS
                else:
                    raise ValueError("Unknown mode: {}".format(mode))
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
            # Handle the nargs
            if 'nargs' in arg:
                # Assign sensible defaults
                if 'default' not in arg:
                    if arg['nargs'] in ['*', '+']:
                        arg['default'] = []
                    else:
                        # The default would usually be None
                        # Use __contains__ to check if argument is present
                        arg['default'] = NoArgument
                        # For '?', the `default` value is used if the option is
                        # not provided; if it is provided but with no argument,
                        # the value from `const` is taken, which defaults to
                        # None
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

        if isinstance(getattr(self.args, arg), list):
            raise AttributeError(
                "tried to check for presence of arg {} on {}, which is a "
                "list".format(arg, self.args)
            )

        return True

    def __getitem__(self, arg):
        """Retrieves argument value via getitem operator"""
        # Cannot access item if the argument was either not provided or if it
        # has no default value.
        if getattr(self.args, arg) is NoArgument:
            raise AttributeError(
                "tried to access an argument ({}) that either wasn't given "
                "or has no default value".format(arg)
            )
        # Return either the given value or the default value
        return getattr(self.args, arg)

    def __setitem__(self, arg, value):
        """Sets the value of an argument. Should only be used to modify
        existing arguments."""
        setattr(self.args, arg, value)

    def __len__(self):
        """Get the number of arguments given to this command"""
        return len(vars(self.args))

    @abstractmethod
    def execute(self, irc_c, msg, cmd):
        """Method to be called when this command is run that implements its
        functionality."""
