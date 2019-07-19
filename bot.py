#!/usr/bin/env python

from pyaib.ircbot import IrcBot
import sys

argv = sys.argv[1:]
bot = IrcBot(argv[0] if argv else 'tars.conf')

# Bot takeover
try:
    bot.run()
except KeyboardInterrupt:
    # do something to handle bot shutdown
    print("The bot has stoppeth!")
    pass
