"""registry.py

Helpers for the command registry (commands/__init__.py).
"""

from importlib import import_module, reload
import sys

from tars.helpers.basecommand import Command


def cmdprint(text, error=False):
    """Prints a pretty-formatted print to the console."""
    bit = "[\x1b[38;5;75mCommands\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))


class CommandsRegistry:
    """Wrapper for the object that contains all the registered commands."""

    def __init__(self, registry):
        """The input registry should be a dict of lists."""
        # The registry contains the command locations and aliases as declared
        # by the bot owner
        self._registry = registry
        # The internal alias store contains the commands themselves, mapped
        # to each alias
        self._aliased_commands = {}
        # The internal commands store contains the commands mapped to their own
        # class name for documentation convenience
        self._commands = {}

        # Bind all the registered commands to the internal commands store
        for file in self.list_registered_files():
            try:
                if "tars.commands.{}".format(file) not in sys.modules:
                    # If the file's module is not already loaded, import it -
                    # this will happen when the bot is booted
                    module = import_module(".{}".format(file), "tars.commands")
                else:
                    # If the module is already in memory, reload it - this will
                    # happen when commands are reloaded (.reload)
                    module = reload(
                        sys.modules["tars.commands.{}".format(file)]
                    )
                # Iterate through the registered commands in this file, which
                # should correspond to class names in the module
                for command_name in self.list_registered_commands(file):
                    cmdprint("Importing {} from {}".format(command_name, file))
                    command_class = getattr(module, command_name)
                    if not issubclass(command_class, Command):
                        raise TypeError(
                            "Command '{}' in '{}' does not extend the base "
                            "command".format(command_name, file)
                        )
                    # Extend the internal alias store with the map of this
                    # command's aliases to the command itself
                    self._aliased_commands.update(
                        {
                            alias: command_class
                            for alias in command_class.aliases
                        }
                    )
                    # Extend the internal command store with this command's
                    # class name and the class itself, for easy access by the
                    # documentation generator
                    self._commands[command_name] = command_class
            except AttributeError as error:
                # If the file or command does not exist, report it, but
                # continue loading commands
                cmdprint(error, True)

    def list_registered_files(self):
        """Gets the list of registered command files."""
        return self._registry.keys()

    def list_registered_commands(self, file):
        """Gets the list of registered commands in the given command file."""
        return self._registry[file]

    def list_all_commands(self):
        """List all registered commands regardless of file."""
        return [
            command
            for file in self._registry
            for command in self._registry[file]
        ]

    def list_all_aliases(self):
        """List all registered aliases regardless of command."""
        return [
            alias
            for file in self._registry
            for command in self._registry[file]
            for alias in self._registry[file][command]
        ]

    def get_command_by_alias(self, alias):
        """Gets the command that has the given alias."""
        return self._aliased_commands[alias]

    def get_command_by_name(self, name):
        """Gets a command by its class name."""
        return self._commands[name]

    def anchor(self, alias, argument=None):
        """Makes the anchor that will link to the given command or the given
        argument.

        Returns a tuple of length 0 if the command does not exist, length 1 if
        the command exists but the argument doesn't, and length 2 if they both
        exist. The first item is the command class, the second item is the
        argument.
        """
        try:
            command = self.get_command_by_alias(alias)
        except KeyError:
            return ()
        if argument is None:
            return (command,)
        argument = command.get_argument(argument)
        if argument is None:
            return (command,)
        return (command, argument)
