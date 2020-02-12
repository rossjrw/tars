'''Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
'''

# Hey there deadname, I haven't seen you go by this name before.
# Would you consider adding this name to your list of alises by
# typing `.alias newname`?

import re
from pyaib.plugins import observe, plugin_class
from pyaib.signals import emit_signal
from helpers.parse import nickColor
from helpers.database import DB
from helpers.defer import defer

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
        nicks = re.split(r"\s:?", msg.args.strip())
        nicks = nicks[2:]
        channel = nicks.pop(0)
        names = [{'nick': name} for name in nicks]
        # chatstaff names start with a punctuation
        for key, name in enumerate(names):
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
        nameprint("Updating NAMES for {}: {}".format(
            nickColor(channel),
            ", ".join(nickColor(nick) for nick in sorted(nicks))))
        try:
            DB.sort_names(channel, names)
        except Exception as e:
            irc_c.RAW("PRIVMSG #tars NAMES error: " + str(e))
            raise
        finally:
            # broadcast this info to whatever needs it
            emit_signal(irc_c, 'NAMES_RESPONSE')

    @observe('IRC_MSG_NICK') # someone changes their name
    def change_name(self, irc_c, msg):
        assert msg.kind == 'NICK'
        nameprint("{} changed their name to {}".format(msg.nick, msg.args))
        try:
            DB.rename_user(msg.nick, msg.args)
        except Exception as e:
            irc_c.RAW("PRIVMSG #tars NAMES error: " + str(e))
            raise

    @observe('IRC_MSG_JOIN')
    def join_names(self, irc_c, msg):
        # make sure the names are always up to date
        defer.get_users(irc_c, msg.raw_channel)

    @observe('IRC_MSG_PART')
    def part_names(self, irc_c, msg):
        # make sure the names are always up to date
        for channel in DB.get_all_channels():
            defer.get_users(irc_c, channel)
