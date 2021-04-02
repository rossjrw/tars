"""extract.py

Extracts documentation information from the command registry.
"""

import re

from tars.commands import COMMANDS_REGISTRY
from tars.helpers.basecommand import Command
from tars.helpers.defer import deferred_bots_for_alias


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


def get_info_from_command(ThisCommand):
    """Extracts information about a command from its class."""
    assert issubclass(ThisCommand, Command)
    if ThisCommand.command_name is None:
        # This command does not want to be documented
        return None
    # Get the command's parent
    ParentCommand = ThisCommand.__mro__[1]
    # Sort deferred aliases into a sensible structure
    deferral_conditions = {
        alias: deferred_bots_for_alias(alias)
        for alias in ThisCommand.aliases
        if len(deferred_bots_for_alias(alias).keys()) > 0
    }
    ref = str
    unique_deferral_conditions = set(
        [ref(condition) for condition in deferral_conditions.values()]
    )
    defers_to = [
        {
            'aliases': [
                alias
                for alias, condition in deferral_conditions.items()
                if ref(condition) == c
            ],
            'condition': [
                condition
                for condition in deferral_conditions.values()
                if ref(condition) == c
            ][0],
        }
        for c in unique_deferral_conditions
    ]
    # Construct the rest of the command info
    info = {
        'id': ThisCommand.__name__,
        'name': ThisCommand.command_name,
        'help': dedent_docstring(ThisCommand.__doc__),
        'arguments': [
            {
                'id': "{}-{}".format(
                    ThisCommand.__name__.lower(), arg['flags'][0].lstrip("-")
                ),
                **arg,
                'help': dedent_docstring(arg['help']),
                'type': arg['type'].__name__,
            }
            for arg in ThisCommand.arguments
            if arg.get('mode', "") != 'hidden'
            and (
                # Do not include arguments from parent commands
                ParentCommand is Command
                or arg not in ParentCommand.arguments
            )
        ],
        'aliases': ThisCommand.aliases,
        'defersTo': defers_to,
        'usage': ThisCommand(ignore_permission_check).get_parser().get_usage(),
        'base': ParentCommand.__name__,
    }
    return info


def dedent_docstring(docstring):
    """Removes indentation from the start of a multiline docstring."""
    if docstring is None:
        return ""
    # Remove all indentation
    # Note that this effectively disables Markdown features like indented code
    # blocks/lists - if I want these in the future, I will have to replace this
    # with a less naive method. textwrap.dedent is not appropriate because the
    # first line of a docstring typically has no indentation.
    return re.sub(r"\n[ \t]*", "\n", docstring)


def ignore_permission_check(*_):
    """A permission checker that ignores the permission level and always
    passes."""
    return True
