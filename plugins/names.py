'''Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
'''

# Hey there deadname, I haven't seen you go by this name before.
# Would you consider adding this name to your list of alises by
# typing `.alias newname`?

from pyaib.plugins import observe, plugin_class
import re
from pprint import pprint
from helpers.parse import nickColor
from helpers.database import DB

def nameprint(text, error=False):
    bit = "[\x1b[38;5;218mNames\x1b[0m] "
    if error:
        bit += "[\x1b[38;5;196mError\x1b[0m] "
    print(bit + str(text))

@plugin_class('names')
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
        nameprint("Getting NAMES from {}".format(nickColor(channel)))
        try:
            DB.sort_names(channel, names)
        except Exception as e:
            irc_c.RAW("PRIVMSG #tars NAMES error: " + str(e))
            raise

    @observe('IRC_MSG_NICK') # someone changes their name
    def change_name(self, irc_c, msg):
        assert msg.kind == 'NICK'
        nameprint("{} changed their name to {}".format(msg.nick, msg.args))
        try:
            DB.rename_user(msg.nick, msg.args)
        except Exception as e:
            irc_c.RAW("PRIVMSG #tars NAMES error: " + str(e))
            raise

