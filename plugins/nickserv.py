#!/usr/bin/env python
#
# Handler for nickserv registration

from pyaib.plugins import plugin_class, observes
import sys

# Let pyaib know that this is a plugin class
# Store the address of the class at 'nickserv' in the context obj
@plugin_class("nickserv")
class NickServ(object):
    def __init__(self, irc_context, config):
        self.config = config
        self.password = config.get("password")

    @observes("IRC_ONCONNECT")
    def AUTO_IDENTIFY(self, irc_context):
        self.identify(irc_context)

        # Spawn a watcher that makes sure we have the nick
        irc_context.timers.clear("nickserv", self.watcher)
        irc_context.timers.set("nickserv", self.watcher, every=90)

    def watcher(self, irc_context, timertext):
        if irc_context.botnick != irc_context.config.irc.nick:
            self.identify(irc_context)

    def identify(self, irc_context):
        if irc_context.botnick != irc_context.config.irc.nick:
            print("Trying to reacquire nick...")
            irc_context.PRIVMSG("nickserv",
                                "GHOST {} {}".format(
                                    irc_context.config.irc.nick,
                                    self.password))
            irc_context.NICK(irc_context.config.irc.nick)

        # Identify
        print("Idenfifying with nickserv...")
        irc_context.PRIVMSG("nickserv",
                            "IDENTIFY {}".format(self.password))
        print(">>> IDENTIFY {}".format(self.password) + " <<<")
