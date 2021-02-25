#!/usr/bin/env python

import argparse
import time

from pyaib.ircbot import IrcBot


def takeover(bot):
    """Starts the pyaib bot"""
    try:
        bot.run()
    except ConnectionResetError:
        print(
            "[\x1b[38;5;196mError\x1b[0m] Connection reset, trying again in 5 minutes"
        )
        time.sleep(60)
        takeover(bot)
    except Exception as e:
        print("CAUGHT {0}".format(e))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Command-line interface for TARS."""
    )
    parser.add_argument(
        'config',
        type=str,
        nargs=None,
        help="""The config file for the bot.""",
    )
    args = parser.parse_args()
    # Pyaib wants the config file name and the path separately
    config_path, _, config_file = args.config.rpartition("/")
    takeover(IrcBot(config_file, config_path))
