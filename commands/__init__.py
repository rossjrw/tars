"""commands/__init__.py

Add commands to the following dict.
The key must be the filename.
The value must be a dict of commands in that file.
Those values must be a list of aliases for that command.

COMMANDS = {
    "file": {"commandname": {"alias1","alias2"}}
}
"""

COMMANDS = {
    "search": {"search": {"search","sea","s"},
               "regexsearch": {"regexsearch","rsearch","rsea","rs"},
               "tags": {"tags"},
               "lastcreated": {"lastcreated","lc","l"},
              },
    "showmore": {"showmore": {"showmore","sm","pick"},
                },
    "admin": {"kill": {"kys"},
              "join": {"join","rejoin"},
              "leave": {"leave","part"},
              "reload": {"reload"},
              "say": {"say"},
              "config": {"config"},
              "reboot": {"reboot"},
              "debug": {"debug"},
              "update": {"update"},
             },
    "refactor": {"refactor": {"refactor"},
                },
    "chevron": {"chevron": {"chevron"},
               },
    "info": {"help": {"help"},
             "status": {"tars","version","status","uptime"},
             "github": {"github","gh"},
             "user": {"user"},
             "tag": {"tag"},
            },
    "promote": {"promote": {"promote"},
               },
    "gimmick": {"reptile": {"reptile","rep"},
                "fish": {"fish","reptile+","rep+"},
                "bear": {"bear"},
                "narcissism": {"rounderhouse","jazstar","themightymcb"},
                "password": {"password","passcode"},
                "hug": {"hug","hugtars"},
                "fiction": {"isthisreal"},
               },
    "converse": {"converse": {"converse"},
                },
    "dbq": {"query": {"query","dbq"},
           },
    "record": {"record": {"record"},
               "pingall": {"pingall"},
              },
    "prop": {"propagate": {"propagate","prop"},
            },
    "analytic": {"analyse_wiki": {"analyse_wiki"},
                },
    "gib": {"gib": {"gib"},
           },
    "nick": {"alias": {"alias"},
                },
}

from helpers.error import CommandNotExistError

class Commands_Directory:
    def __init__(self, directory):
        self.COMMANDS = directory

    def get(self,file=None,command=None):
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
        import_module(".{}".format(file),"commands")
    for cmd in COMMANDS.get(file):
        cmdprint("Importing {} from {}".format(cmd,file))
        for alias in COMMANDS.get(file,cmd):
            try:
                setattr(COMMANDS, alias, getattr(locals()[file], cmd))
            except AttributeError as e:
                cmdprint(e, True)
                # consider stopping the script here
        # now each command is at commands.file.cmdname.command()
