#!/usr/bin/env python
#
# Handler for nickserv registration

from pyaib.plugins import plugin_class, observes
import sys
import os.path

# Let pyaib know that this is a plugin class
# Store the address of the class at 'nickserv' in the context obj
@plugin_class("nickserv")
class NickServ(object):
    def __init__(self, irc_c, config):
        self.config = config
        passfile = open(os.path.dirname(__file__)
                        + "/../password.secret.txt")
        self.password = passfile.readline()
        passfile.close()

    @observes("IRC_ONCONNECT")
    def AUTO_IDENTIFY(self, irc_c):
        self.identify(irc_c)

        # Spawn a watcher that makes sure we have the nick
        irc_c.timers.clear("nickserv", self.watcher)
        irc_c.timers.set("nickserv", self.watcher, every=90)

    def watcher(self, irc_c, timertext):
        if irc_c.botnick != irc_c.config.irc.nick:
            self.identify(irc_c)

    def identify(self, irc_c):
        if irc_c.botnick != irc_c.config.irc.nick:
            print("Trying to reacquire nick...")
            irc_c.PRIVMSG("nickserv",
                                "GHOST {} {}".format(
                                    irc_c.config.irc.nick,
                                    self.password))
            irc_c.NICK(irc_c.config.irc.nick)

        # Identify
        print("Idenfifying with nickserv...")
        irc_c.PRIVMSG("nickserv",
                      "IDENTIFY {}".format(self.password))
        print("Marking myself as a bot...")
        irc_c.RAW("/mode TARS +B")
        # Assuming that went correctly, recoonect to channels
        print(irc_c.channels.channels)
        if irc_c.config.channels.autojoin:
            irc_c.JOIN("#tars")
            for channel in irc_c.config.channels.autojoin:
                irc_c.JOIN(channel)
                print("Joining " + str(channel))
