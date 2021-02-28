"""converse.py

Responses for regular messages - ie, not commands.
Adding anything to this that doesn't refer directly to TARS is 100% a dick move
and should never be done.

After a converse, unless you want the potential for a further converse to
occur, return.
"""

import json
import re
import string

from fuzzywuzzy import fuzz

import tars.commands
from tars.helpers.basecommand import Command
from tars.helpers.config import CONFIG
from tars.helpers.database import DB
from tars.helpers.defer import defer
from tars.helpers.greetings import acronym, greet, greets


def chunks(array, length):
    """Splits list into lists of given length"""
    for i in range(0, len(array), length):
        yield array[i : i + length]


class Converse(Command):
    """An internal command used to respond to non-command messages."""

    command_name = "search"
    arguments = [
        dict(
            flags=['message'],
            type=str,
            nargs='*',
            help="""The message to respond to.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):

        ##### ping matches #####

        if cmd.ping:
            if any(
                x in cmd.message.lower()
                for x in ["fuck you", "piss off", "fuck off",]
            ):
                msg.reply("{}: no u".format(msg.nick))
                return

        ##### ping-optional text matches #####

        if cmd.message.startswith("?? "):
            # CROM compatibility
            # Manually parse and instantiate a search command
            # Duplication of code in plugins/parsemessages.py - TODO unify
            command_class = tars.commands.COMMANDS_REGISTRY.get_command(
                'search'
            )
            command = command_class()
            command.parse(cmd.message)
            command.execute(irc_c, msg, cmd)
            return
        if msg.message.lower() == "{}!".format(CONFIG.nick.lower()):
            msg.reply("{}!".format(msg.nick))
            return
        if strip(msg.message.lower()) in [
            strip("{}{}".format(g, CONFIG.nick.lower())) for g in greets
        ]:
            if msg.sender == 'XilasCrowe':
                msg.reply("toast")
                return
            msg.reply(greet(msg.nick))
            return
        if (
            CONFIG.nick == "TARS"
            and matches_any_of(
                msg.message,
                ["what does tars stand for?", "is tars an acronym?",],
            )
            and "TARS" in msg.message.upper()
        ):
            msg.reply(acronym())
            return
        if (
            CONFIG.nick == "TARS"
            and matches_any_of(
                msg.message, ["is tars a bot?", "tars are you a bot?",]
            )
            and "TARS" in msg.message.upper()
        ):
            msg.reply("Yep.")
            return
        if (
            CONFIG.nick == "TARS"
            and matches_any_of(
                msg.message, ["is tars a person?", "tars are you a person?",]
            )
            and "TARS" in msg.message.upper()
        ):
            msg.reply("Nope. I'm a bot.")
            return
        if (
            CONFIG.nick == "TARS"
            and matches_any_of(msg.message, ["what is your iq",])
            and "TARS" in msg.message.upper()
        ):
            msg.reply("big")
            return
        if (
            CONFIG.nick == "TARS"
            and matches_any_of(msg.message, ["damn you to hell",])
            and "TARS" in msg.message.upper()
        ):
            msg.reply("damn me to hell")
            return

        ##### regex matches #####

        # give url for reddit links
        match = re.search(r"(?:^|\s)/?r/(\S*)", msg.message, re.IGNORECASE)
        if match:
            msg.reply("https://www.reddit.com/r/{}".format(match.group(1)))
            return
        # tell me about new acronyms
        acronyms = find_acronym(msg.message, CONFIG['IRC']['nick'])
        if acronyms:
            raw_acronym, bold_acronym = acronyms
            with open(CONFIG['converse']['acronyms'], 'r') as acro_file:
                acros = json.load(acro_file)
                existing_acronyms = [acro['acronym'] for acro in acros]
            if raw_acronym not in existing_acronyms:
                msg.reply(bold_acronym)
                if msg.raw_channel != CONFIG['channels']['home']:
                    defer.report(cmd, bold_acronym)
                with open(CONFIG['converse']['acronyms'], 'w') as acro_file:
                    acros.append(
                        {
                            'acronym': raw_acronym,
                            'sender': msg.nick,
                            'channel': msg.raw_channel,
                            'date': msg.timestamp,
                        }
                    )
                    json.dump(acros, acro_file, indent=2)
                return

        ##### custom matches #####

        if (
            msg.sender == "Jazstar"
            and "slime" in msg.message
            and "XilasCrowe" in DB.get_channel_members(msg.raw_channel)
        ):
            msg.reply("Oi xilas I heard you like slime!")
            return

        # after all attempts, must indicate failure if pinged
        if cmd.ping:
            return 1


def strip(string):
    """Strips all non-alphanumeric characters."""
    return ''.join(l for l in string if l.isalnum()).lower()


def matches_any_of(subject, matches, threshold=80):
    for match in matches:
        if fuzz.ratio(subject.lower(), match) >= threshold:
            return True
    return False


def find_acronym(message, acro_letters):
    match = re.search(
        r"(\s+|(?:\s*[{0}]+\s*))".join(
            [
                r"([{{0}}]*)\b({})(\S*)\b([{{0}}]*)".format(l)
                for l in acro_letters
            ]
        ).format(re.escape(string.punctuation)),
        message,
        re.IGNORECASE | re.VERBOSE,
    )
    if match:
        raw_acronym = "".join(match.groups())
        submatches = list(chunks(list(match.groups()), 5))
        # the match is made up of 5 repeating parts:
        # 0. punctation before word
        # 1. first letter of word
        # 2. rest of word
        # 3. punctuation after word
        # 4. stuff between this word and the next word
        # for the last word (submatch), however, 4 is not present
        submatches[-1].append("")
        for submatch in submatches:
            submatch[1] = submatch[1].upper()
        bold_acronym = "".join(
            ["{}\x02{}\x0F{}{}{}".format(*submatch) for submatch in submatches]
        )
        return raw_acronym, bold_acronym
    return False
