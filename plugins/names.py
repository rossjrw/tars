"""Names Plugin

Whenever we gets a NAMES response from the server, save that info to the db.
"""

from pyaib.plugins import observe, plugin_class

@plugin_class('names')
class Names:
    def __init__(self, irc_c, config):
        print("Names Plugin Loaded!")

    @observe('IRC_MSG')
    def record_names(self, irc_c, msg):
        print("[Names] {}".format(msg.kind))
