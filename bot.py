#!/usr/bin/env python

from pyaib.ircbot import IrcBot
import sys
import argparse
from gevent import monkey
monkey.patch_all()

bot = IrcBot('bot.conf')

# Bot takeover
try:
    bot.run()
except KeyboardInterrupt:
    # do something to handle bot shutdown
    print("The bot has stoppeth!")
    pass
