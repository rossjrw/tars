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


def get_args_from_command_line():
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(
        description="""Command-line interface for TARS."""
    )
    parser.add_argument(
        'config',
        type=str,
        nargs=None,
        help="""The config file (YAML) for the bot.""",
    )
    parser.add_argument(
        '--deferral',
        type=str,
        nargs=None,
        default=None,
        help="""The config file (TOML) for which commands defer to other
        bots.""",
    )
    parser.add_argument(
        '--docs',
        default=False,
        action='store_true',
        help="""Instead of running the bot, build the documentation.""",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args_from_command_line()
    if args.docs:
        from tars.documentation.build import build

        build()
    else:
        # Run the bot
        config = get_args_from_command_line().config
        # Pyaib wants the config file name and the path separately
        config_path, _, config_file = config.rpartition("/")
        takeover(IrcBot(config_file, config_path))
