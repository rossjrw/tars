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
        help="""The config file for the bot.""",
    )
    parser.add_argument(
        '--docs',
        default=False,
        action='store_true',
        help="""Instead of running the bot, build the documentation.""",
    )
    return parser.parse_args()


def get_config_from_command_line():
    """Gets the specified config file name from the command line invocation"""
    return get_args_from_command_line().config


if __name__ == "__main__":
    args = get_args_from_command_line()
    if args.docs:
        from tars.documentation.build import build

        build()
    else:
        # Run the bot
        config = get_config_from_command_line()
        # Pyaib wants the config file name and the path separately
        config_path, _, config_file = config.rpartition("/")
        takeover(IrcBot(config_file, config_path))
