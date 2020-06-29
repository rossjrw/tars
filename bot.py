#!/usr/bin/env python

from pyaib.ircbot import IrcBot
import sys
import time

argv = sys.argv[1:]
bot = IrcBot(argv[0] if argv else 'tars.conf')

# Bot takeover
def takeover():
    try:
        bot.run()
    except ConnectionResetError:
        print(
            "[\x1b[38;5;196mError\x1b[0m] Connection reset, trying again in 5 minutes"
        )
        time.sleep(60)
        takeover()
    except Exception as e:
        print("CAUGHT {0}".format(e))
        raise


takeover()
