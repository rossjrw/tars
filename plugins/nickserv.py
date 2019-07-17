#!/usr/bin/env python
#
# Handler for nickserv registration

from pyaib.plugins import plugin_class, observes
import sys
import os.path
from time import sleep
from helpers.greetings import greet
from helpers.api import password

def nsprint(message):
    print("[\x1b[38;5;212mNickServ\x1b[0m] " + str(message))

# Let pyaib know that this is a plugin class
# Store the address of the class at 'nickserv' in the context obj
@plugin_class("nickserv")
class NickServ(object):
    def __init__(self, irc_c, config):
        self.config = config
        self.password = password

    @observes("IRC_ONCONNECT")
    def AUTO_IDENTIFY(self, irc_c):
        self.identify(irc_c)

        # Spawn a watcher that makes sure we have the nick
        irc_c.timers.clear("nickserv", self.watcher)
        irc_c.timers.set("nickserv", self.watcher, every=90)

        # Assuming that went correctly, recoonect to channels
        nsprint("{}".format(irc_c.config.channels))

    def watcher(self, irc_c, timertext):
        if irc_c.botnick != irc_c.config.irc.nick:
            self.identify(irc_c)

    def identify(self, irc_c):
        if irc_c.botnick != irc_c.config.irc.nick:
            nsprint("Trying to reacquire nick...")
            irc_c.PRIVMSG("nickserv",
                          "GHOST {} {}".format(
                                    irc_c.config.irc.nick,
                                    self.password))
            irc_c.NICK(irc_c.config.irc.nick)

        # Identify
        nsprint("Idenfifying with nickserv...")
        irc_c.PRIVMSG("nickserv",
                      "IDENTIFY {}".format(self.password))
        nsprint("Marking myself as a bot...")
        irc_c.RAW("mode TARS +B")

    @observes("IRC_MSG_NOTICE")
    def autojoin(self, irc_c, msg):
        if "Password accepted" in msg.message:
            if irc_c.config.channels.autojoin:
                for channel in irc_c.config.channels.autojoin:
                    irc_c.JOIN(channel)
                    nsprint("Joining " + str(channel))
            # Now we need to join the autojoin channels from the db
            # but we'll do this later
