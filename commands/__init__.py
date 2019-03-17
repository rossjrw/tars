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
    "colour": {"colour": {"colour"},
              },
    "search": {"search": {"search","sea","s"},
               "regexsearch": {"regexsearch","rsearch","rsea","rs"},
               "tags": {"tags"},
              },
}

class Commands_Directory:
    def __init__(self):
        self.COMMANDS = COMMANDS

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

class Object_Alias:
    pass

from importlib import import_module

def cmdprint(text, error=False):
    bit = "[\x1b[38;5;75mCommands\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

COMMANDS = Commands_Directory()

for file in COMMANDS.get():
    cmdprint("Importing commands from commands/{}.py".format(file))
    import_module(".{}".format(file),"commands")
    for cmd in COMMANDS.get(file):
        cmdprint("Importing {}".format(cmd))
        try:
            search.regexsearch().test()
            # ^ this works - need to alias the aliases
            # alias search.regexsearch().command()
            # to commands.regexsearch().command()
        except NameError:
            cmdprint("search doesn't exist", True)
        for alias in COMMANDS.get(file,cmd):
            setattr(COMMANDS, alias, getattr(locals()[file], cmd))
            pass
    import_module(".{}".format(file),"commands")
    # now each command is at commands.file.cmdname.command()
    # but we want to skip the file step, ideally
