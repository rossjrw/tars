"""Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
"""

from pyaib.plugins import observe, plugin_class

@plugin_class('names')
class Names:
    def __init__(self, irc_c, config):
        print("Names Plugin Loaded!")

    @observe('IRC_MSG_353') # 353 is a NAMES response
    def record_names(self, irc_c, msg):
        # the names are in msg.args but as individual letters
        saving  = False
        names = []
        name = ""
        for letter in msg.args:
            # we don't want to keep any letters until we get to a colon
            if saving:
                if letter is not ' ':
                    name += letter
                else:
                    names.append(name)
                    name = ""
            elif letter == ':':
                saving = True
        # chatstaff names start with a punctuation
        # for consistency, let's add a char to identify names with no role
        for key,name in enumerate(names):
            print(name[0])
            if name[0] in "~&@%+":
                # they have a role, do nothing
                pass
            else:
                names[key] = "-" + name
        print(names)
