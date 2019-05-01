#!/usr/bin/env python

from pyaib.ircbot import IrcBot
import sys
import argparse
try:
    from helpers.database import Database
except ImportError:
    print("Database module is missing")
    raise

# Parse the command line argument
parser = argparse.ArgumentParser(description="TARS bot")
parser.add_argument("-n","--nick",
                    help="Nickname of the bot, defaults via config")
parser.add_argument("-p","--password",
                    help="Password for nickserv identification")
parser.add_argument("-c","--config",default="bot.conf",
                    help="Configuration file, defaults to bot.conf")
args = parser.parse_args()

if args.password:
    # save the password to a file
    print("Caching password...")
    file = open("password.secret.txt","w")
    file.write(args.password)
    file.close()
else:
    print("You didn't specify a password")

# Load "bot.conf"
bot = IrcBot(args.config)

# Bot takeover
try:
    bot.run()
except KeyboardInterrupt:
    # do something to handle bot shutdown
    print("The bot has stoppeth!")
    pass
