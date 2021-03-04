"""commands/__init__.py

This file is a declaration of all commands available to TARS, and tells TARS
both where to find them (by listing their file name and class name) and how a
user should access them (by listing their command-line aliases).

A command that is written (i.e. that exists and is in the commands/ dir) will
not appear in documentation and will not be available to the user unless it is
registered here.

Add commands to the following dict.
The key must be the filename.
The value must be a dict of commands in that file.
Those values must be a list of aliases for that command, of which the first is
considered the command's canonical alias.

COMMANDS_REGISTRY = {
    "file": {"Commandname": {"alias1","alias2"}}
}
"""

from tars.helpers.registry import CommandsRegistry

COMMANDS_REGISTRY = CommandsRegistry(
    {
        # Searching
        "search": {
            "Search": ["search", "sea", "s"],
            "Regexsearch": ["regexsearch", "rsearch", "rsea", "rs"],
            "Tags": ["tags"],
            "Lastcreated": ["lastcreated", "lc", "l"],
        },
        "showmore": {"Showmore": ["showmore", "sm", "pick"],},
        "shortest": {"Shortest": ["shortest"]},
        # Database manipulation
        "propagate": {"Propagate": ["propagate", "prop"],},
        "dbq": {"Query": ["dbq"], "Seen": ["seen", "lastseen"],},
        "refactor": {"Refactor": ["refactor"],},
        "nick": {"Alias": ["alias"],},
        # Staff tools
        "pingall": {"Pingall": ["pingall"],},
        "promote": {"Promote": ["promote"],},
        # Internal commands
        "admin": {
            "Kill": ["kill", "kys"],
            "Join": ["join", "rejoin"],
            "Leave": ["leave", "part"],
            "Reload": ["reload"],
            "Say": ["say"],
            "Config": ["config"],
            "Reboot": ["reboot"],
            "Debug": ["debug"],
            "Update": ["update"],
            "Helenhere": ["helenhere"],
        },
        "converse": {"Converse": ["converse"],},
        # Information retrieval
        "info": {
            "Help": ["help"],
            "Status": ["status", "tars"],
            "Github": ["github", "gh"],
            "User": ["user"],
            "Tag": ["tag"],
        },
        "gimmick": {
            "Reptile": ["reptile", "rep"],
            "Fish": ["fish", "reptile+", "rep+"],
            "Bear": ["bear"],
            "Cat": ["cat"],
            "Balls": ["balls"],
            "Narcissism": ["rounderhouse", "jazstar", "themightymcb"],
            "Password": ["passcode"],
            "Hug": ["hug", "hugtars"],
            "Fiction": ["isthisreal"],
            "Idea": ["idea"],
            "Punctuation": ["punctuation", "punc", "blackbox"],
            "Tell": ["tell"],
        },
        # Other
        "gib": {
            "Gib": ["gib", "gibber", "big", "goob", "boog", "gob", "bog"],
        },
    }
)
