'''Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
'''

# Hey there deadname, I haven't seen you go by this name before.
# Would you consider adding this name to your list of alises by
# typing `.alias newname`?

from pyaib.plugins import observe, plugin_class

@plugin_class('names')
class Names:
    def __init__(self, irc_c, config):
        print('Names Plugin Loaded!')

    @observe('IRC_MSG_353') # 353 is a NAMES response
    def record_names(self, irc_c, msg):
        # the names are in msg.args but as individual letters
        saving  = False
        names = []
        name = ''
        for letter in msg.args:
            # we don't want to keep any letters until we get to a colon
            if saving:
                if letter is not ' ':
                    name += letter
                else:
                    names.append({'nick': name})
                    name = ''
            elif letter == ':':
                saving = True
        # chatstaff names start with a punctuation
        # for consistency, let's add a char to identify names with no role
        modes = ['vop','hop','aop','sop','owner']
        modechars = '+%@&~'
        for key,name in enumerate(names):
            if name['nick'][0] in modechars:
                # Set the user mode based on the first character
                names[key] = {
                    'nick': name['nick'][1:],
                    'mode': modes[modechars.index(name['nick'][0])]
                }
            else:
                names[key] = {
                    'nick': name['nick'],
                    'mode': None
                }
        # just need to log these names to the db now
