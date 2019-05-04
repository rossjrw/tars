'''Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
'''

# Hey there deadname, I haven't seen you go by this name before.
# Would you consider adding this name to your list of alises by
# typing `.alias newname`?

from pyaib.plugins import observe, plugin_class
import re
from pprint import pprint

@plugin_class('names')
@plugin_class.requires('db')
class Names:
    def __init__(self, irc_c, config):
        print('Names Plugin Loaded!')

    @observe('IRC_MSG_353') # 353 is a NAMES response
    def record_names(self, irc_c, msg):
        # msg.args is a string
        # "TARS = #channel :name1 name2 name3 name4"
        names = re.split(r"\s:?", msg.args.strip())
        names = names[2:]
        channel = names.pop(0)
        names = [{'nick': name} for name in names]
        # chatstaff names start with a punctuation
        for key,name in enumerate(names):
            if name['nick'][0] in '+%@&~':
                names[key] = {
                    'nick': name['nick'][1:],
                    'mode': name['nick'][0]
                }
            else:
                names[key] = {
                    'nick': name['nick'],
                    'mode': None
                }
        # just need to log these names to the db now
        pprint(names)
        irc_c.db._driver.sort_names(channel, names)
