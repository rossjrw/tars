"""extract.py

Extracts documentation information from the command registry.
"""

import re

from tars.commands import COMMANDS_REGISTRY
from tars.helpers.basecommand import Command


def get_command_info():
    """Gets the documentation info for each registered command."""
    infos = []
    for file in COMMANDS_REGISTRY.list_registered_files():
        for command_name in COMMANDS_REGISTRY.list_registered_commands(file):
            infos.append(
                get_info_from_command(
                    COMMANDS_REGISTRY.get_command_by_name(command_name)
                )
            )
    infos = [info for info in infos if info is not None]
    return infos


def get_info_from_command(command_class):
    """Extracts information about a command from its class."""
    assert issubclass(command_class, Command)
    if command_class.command_name is None:
        # This command does not want to be documented
        return None
    basecommand = command_class.__mro__[1]
    info = {
        'id': command_class.__name__,
        'name': command_class.command_name,
        'help': dedent_docstring(command_class.__doc__),
        'defers_to': command_class.defers_to,
        'arguments': [
            {
                'id': "{}-{}".format(
                    command_class.__name__.lower(), arg['flags'][0].lstrip("-")
                ),
                **arg,
                'help': dedent_docstring(arg['help']),
                'type': arg['type'].__name__,
            }
            for arg in command_class.arguments
            if arg.get('mode', "") != 'hidden'
            and (
                # Do not include arguments from parent commands
                basecommand is Command
                or arg not in basecommand.arguments
            )
        ],
        'aliases': command_class.aliases,
        'usage': command_class().get_parser().get_usage(),
        'base': basecommand.__name__,
    }
    return info


def dedent_docstring(docstring):
    """Removes indentation from the start of a multiline docstring."""
    if docstring is None:
        return ""
    # Remove all indentation
    # Note that this effectively disables Markdown features like code blocks -
    # if I want these in the future, I will have to replace this with a less
    # naive method. textwrap.dedent is not appropriate because the first line
    # of a docstring has no indentation.
    return re.sub(r"\n[ \t]*", "\n", docstring)
