# List of commands
# To add a new command:
    # 1. Programme it here
    # 2. Add it to COMMANDS in parsemessages.py
# Commands take the following arguments:
    # irc_c
    # msg (original message object)
    # cmd (msg.parsed)

from ..helpers import parse

def colour(irc_c, msg, cmd):
    msg.reply(parse.nickColor(msg.message))

def search(irc_c, msg, cmd):
    msg.reply("I don't know how to search just yet, sorry.")
