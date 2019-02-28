#!/usr/bin/env python

from pyaib.ircbot import IrcBot
import sys
import argparse

# Parse the command line argument
parser = argparse.ArgumentParser(description="TARS bot")
parser.add_argument("nick",
                    help="Nickname of the bot, defaults via config")
parser.add_argument("-p","--password",
                    help="Password for nickserv identification")
parser.add_argument("-c","--config",default="bot.conf",
                    help="Configuration file, defaults to bot.conf")
args = parser.parse_args()

# Load "bot.conf"
bot = IrcBot(args.config)
print(">>> Current password is " + bot.config.plugin.nickserv.password + " <<<")
print(">>> Changing password to " + args.password + " <<<")
bot.config.plugin.nickserv.password = args.password
print(">>> New password is " + bot.config.plugin.nickserv.password + " <<<")

# Bot takeover
try:
    bot.run()
    pass
except KeyboardInterrupt:
    # do something to handle bot shutdown
    pass
