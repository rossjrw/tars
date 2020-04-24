"""converse.py

Responses for regular messages - ie, not commands.
Adding anything to this that doesn't refer directly to TARS is 100% a dick move
and should never be done.
"""

import re
import string

import commands
from commands.prop import chunks

from fuzzywuzzy import fuzz

from helpers.config import CONFIG
from helpers.database import DB
from helpers.defer import defer
from helpers.greetings import acronym, greet, greets

class converse:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # Recieves text in msg.message
        message = cmd.unping

        ##### ping matches #####

        if cmd.pinged:
            if any(x in message.lower() for x in [
                "fuck you",
                "piss off",
                "fuck off",
            ]):
                msg.reply("{}: no u".format(msg.nick))
                return

        ##### ping-optional text matches #####

        if message.startswith("?? "):
            # CROM compatibility
            getattr(commands.COMMANDS, 'search').command(irc_c, msg, cmd)
        if message.lower() == "{}!".format(CONFIG.nick.lower()):
            msg.reply("{}!".format(msg.nick))
            return
        if strip(message.lower()) in [strip("{}{}".format(g,CONFIG.nick.lower()))
                                      for g in greets]:
            if msg.sender == 'XilasCrowe':
                msg.reply("toast")
                return
            msg.reply(greet(msg.nick))
            return
        if CONFIG.nick == "TARS" and matches_any_of(message, [
            "what does tars stand for?",
            "is tars an acronym?",
        ]) and "TARS" in message.upper():
            msg.reply(acronym())
            return
        if CONFIG.nick == "TARS" and matches_any_of(message, [
            "is tars a bot?",
            "tars are you a bot?",
        ]) and "TARS" in message.upper():
            msg.reply("Yep.")
            return
        if CONFIG.nick == "TARS" and matches_any_of(message, [
            "is tars a person?",
            "tars are you a person?",
        ]) and "TARS" in message.upper():
            msg.reply("Nope. I'm a bot.")
            return
        if CONFIG.nick == "TARS" and matches_any_of(message, [
            "what is your iq",
        ]) and "TARS" in message.upper():
            msg.reply("big")
            return

        ##### regex matches #####

        # tell me about new acronyms
        match = re.search(
            r"(\s+|(?:\s*[{0}]+\s*))".join(
                [r"([{{0}}]*)\b({})(\S*)\b([{{0}}]*)".format(l)
                 for l in CONFIG['IRC']['nick']])
            .format(re.escape(string.punctuation)),
            message, re.IGNORECASE | re.VERBOSE)
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
            with open(CONFIG['converse']['acronyms'], 'r+') as acro:
                existing_acronyms = [strip(line.rstrip('\n')) for line in acro]
            if strip(raw_acronym) not in existing_acronyms:
                for submatch in submatches:
                    submatch[1] = submatch[1].upper()
                bold_acronym = "".join(["{}\x02{}\x0F{}{}{}"
                                        .format(*submatch)
                                        for submatch in submatches])
                msg.reply(bold_acronym)
                if msg.raw_channel != CONFIG['channels']['home']:
                    defer.report(cmd, bold_acronym)
                with open(CONFIG['converse']['acronyms'], 'a') as acro:
                    acro.write(raw_acronym)
                    acro.write("\n")
                return

        ##### custom matches #####

        if (msg.sender == "Jazstar" and
            "slime" in msg.message and
            "XilasCrowe" in DB.get_channel_members(msg.raw_channel)):
            msg.reply("Oy xilas I heard you like slime!")
            return

        # after all attempts, must indicate failure if pinged
        if cmd.pinged:
            return 1

def strip(string):
    """Strips all non-alphanumeric characters."""
    return ''.join(l for l in string if l.isalnum()).lower()

def matches_any_of(subject, matches, threshold=80):
    for match in matches:
        if fuzz.ratio(subject.lower(), match) >= threshold:
            return True
    return False
