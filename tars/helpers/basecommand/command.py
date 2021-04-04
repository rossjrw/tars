"""command.py

Provides the base command class that all commands inherit from.
"""

from abc import ABC, abstractmethod
import shlex

import tars.commands
from tars.helpers.basecommand.parsing import ParsingMixin, NoArgument
from tars.helpers.basecommand.introspection import IntrospectionMixin
from tars.helpers.error import (
    CommandParsingError,
    CommandError,
    CommandParsingHelp,
    CommandUsageMessage,
    MyFaultError,
)


class Command(ABC, ParsingMixin, IntrospectionMixin):
    """Base command extended by all commands that generates documentation from
    its internal argparse object. If this text appears outside of TARS' source
    code, something has gone wrong."""

    # The name of this command as it will appear in documentation; if None, it
    # will not appear
    command_name = None

    # The aliases that can be used to call this command
    aliases = []

    # Whether to suppress errors and help messages
    suppress = False

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
                "You don't have permission to use that command."
            )

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
            raise CommandParsingError(
                "Unmatched quotemark. Use \\\" to escape a literal quotemark"
            ) from e
        message = [w.replace("<<APOS>>", "'") for w in message]
        message = [w.replace("<<QUOT>>", '"') for w in message]
        try:
            # Can throw ArgumentError
            self.args = parser.parse_args(message)
        except CommandParsingHelp as error:
            # The error contains the get_usage string but I'm going to just
            # ignore that
            raise (
                MyFaultError if self.__doc__ is None else CommandUsageMessage
            )(self.make_command_help_string()) from error

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
        """Get the number of arguments given to this command."""
        if self.args is None:
            return 0
        return len(vars(self.args))

    @abstractmethod
    def execute(self, irc_c, msg, cmd):
        """Method to be called when this command is run that implements its
        functionality."""
