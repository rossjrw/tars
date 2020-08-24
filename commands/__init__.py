"""commands/__init__.py

Add commands to the following dict.
The key must be the filename.
The value must be a dict of commands in that file.
Those values must be a list of aliases for that command.

COMMANDS = {
    "file": {"Commandname": {"alias1","alias2"}}
}
"""

from ._command import Command

COMMANDS = {
    "search": {
        "Search": {"search", "sea", "s", "??"},
        "Regexsearch": {"regexsearch", "rsearch", "rsea", "rs"},
        "Tags": {"tags"},
        "Lastcreated": {"lastcreated", "lc", "l"},
    },
    "showmore": {"Showmore": {"showmore", "sm", "pick"},},
    "admin": {
        "Kill": {"kys"},
        "Join": {"join", "rejoin"},
        "Leave": {"leave", "part"},
        "Reload": {"reload"},
        "Say": {"say"},
        "Config": {"config"},
        "Reboot": {"reboot"},
        "Debug": {"debug"},
        "Update": {"update"},
        "Helenhere": {"checkhelen", "helenhere"},
    },
    "refactor": {"Refactor": {"refactor"},},
    "chevron": {"Chevron": {"chevron"},},
    "info": {
        "Help": {"help"},
        "Status": {"tars", "version", "status", "uptime"},
        "Github": {"github", "gh"},
        "User": {"user"},
        "Tag": {"tag"},
    },
    "promote": {"Promote": {"promote"},},
    "gimmick": {
        "Reptile": {"reptile", "rep"},
        "Fish": {"fish", "reptile+", "rep+"},
        "Bear": {"bear"},
        "Cat": {"cat"},
        "Narcissism": {"rounderhouse", "jazstar", "themightymcb"},
        "Password": {"password", "passcode"},
        "Hug": {"hug", "hugtars"},
        "Fiction": {"isthisreal"},
        "Idea": {"idea"},
    },
    "converse": {"Converse": {"converse"},},
    "dbq": {"Query": {"query", "dbq"}, "Seen": {"seen", "lastseen"},},
    "record": {"Record": {"record"}, "Pingall": {"pingall"},},
    "prop": {"Propagate": {"propagate", "prop"},},
    "analytic": {"Analyse_wiki": {"analyse_wiki"},},
    "gib": {"Gib": {"gibber", "gib", "big", "goob", "boog", "gob", "bog"},},
    "nick": {"Alias": {"alias"},},
    "shortest": {"Shortest": {"shortest"}},
}

from helpers.error import CommandNotExistError


class Commands_Directory:
    def __init__(self, directory):
        self.COMMANDS = directory

    def get(self, file=None, command=None):
        if file is None:
            # return a list of files
            return self.COMMANDS.keys()
        else:
            if command is None:
                # return a list of commands in the file
                return self.COMMANDS[file].keys()
            else:
                # return a set of aliases for this command
                return self.COMMANDS[file][command]
        pass

    def __getattr__(self, name):
        """Raise an error when a command doesn't exist"""
        raise CommandNotExistError(name)


from importlib import import_module, reload
import sys


def cmdprint(text, error=False):
    bit = "[\x1b[38;5;75mCommands\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))


COMMANDS = Commands_Directory(COMMANDS)

for file in COMMANDS.get():
    if "commands.{}".format(file) in sys.modules:
        reload(sys.modules["commands.{}".format(file)])
    else:
        import_module(".{}".format(file), "commands")
    for cmd in COMMANDS.get(file):
        cmdprint("Importing {} from {}".format(cmd, file))
        for alias in COMMANDS.get(file, cmd):
            try:
                setattr(COMMANDS, alias, getattr(locals()[file], cmd))
            except AttributeError as e:
                cmdprint(e, True)
                # consider stopping the script here
        # now each command is at commands.file.cmdname.command()
