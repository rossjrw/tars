"""commands/__init__.py

This file is a declaration of all commands available to TARS, and tells TARS
where to find them - in what files they're in, and then what the class name is.

The argument passed to the registry constructor is a dict, where the keys are
the filenames of commands (in the commands/ dir) and the values are a list of
the command classes found in that file.

A command that is written (i.e. that exists and is in the commands/ dir) will
not appear in documentation and will not be available to the user unless it is
registered here.

The order of commands determines what order they appear in in documentation.
"""

from tars.helpers.registry import CommandsRegistry

COMMANDS_REGISTRY = CommandsRegistry(
    {
        # Searching
        "search": ["Search", "Regexsearch", "Tags", "Lastcreated",],
        "showmore": ["Showmore",],
        "shortest": ["Shortest"],
        # Database manipulation
        "propagate": ["Propagate",],
        "dbq": ["Query", "Seen",],
        "refactor": ["Refactor",],
        "nick": ["Alias",],
        # Staff tools
        "pingall": ["Pingall"],
        # Internal commands
        "admin": [
            "Kill",
            "Join",
            "Leave",
            "Reload",
            "Say",
            "Config",
            "Reboot",
            "Debug",
            "Update",
            "Helenhere",
        ],
        "converse": ["Converse",],
        # Information retrieval
        "info": ["Help", "Status", "Github", "User", "Tag",],
        "gimmick": [
            "Reptile",
            "Fish",
            "Bear",
            "Cat",
            "Balls",
            "Narcissism",
            "Password",
            "Hug",
            "Fiction",
            "Idea",
            "Punctuation",
            "Tell",
        ],
        # Other
        "gib": ["Gib",],
    }
)
