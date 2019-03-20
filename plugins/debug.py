""" Debug Plugin (botbot plugins.debug) """
# Copyright 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time
from pyaib.plugins import observe, keyword, plugin_class, every


#Let pyaib know this is a plugin class and to
# Store the address of the class instance at
# 'debug' in the irc_context obj
@plugin_class('debug')
class Debug(object):

    #Get a copy of the irc_context, and a copy of your config
    # So for us it would be 'plugin.debug' in the bot config
    def __init__(self, irc_context, config):
        print("Debug Plugin Loaded!")

    def follow_invites(self, irc_c, msg):
        print(msg.target, irc_c.botnick)
        if msg.target.lower() == irc_c.botnick.lower():  # Sanity
            irc_c.JOIN(msg.message)
            irc_c.PRIVMSG(msg.message, '%s: I have arrived' % msg.nick)
        else:
            msg.reply("Malformed command")
