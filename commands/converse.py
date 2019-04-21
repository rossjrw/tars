"""converse.py

Responses for regular messages - ie, not commands.
Adding anything to this that doesn't refer directly to TARS is 100% a dick move
and should never be done.
"""

from fuzzywuzzy import fuzz
from helpers.greetings import acronym

class converse:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # Recieves text in msg.message
        message = cmd.unping
        # pinged section, for specifics
        if cmd.pinged:
            if any(x in message.lower() for x in [
                "fuck you",
                "piss off",
                "fuck off",
            ]):
                msg.reply("{}: no u".format(msg.nick))
                return
            if message.lower() == "tars!":
                msg.reply("{}!".format(msg.nick))
                return
        # unpinged section
        if matches_any_of(message, [
            "what does tars stand for?",
            "is tars an acronym?",
        ]):
            msg.reply(acronym())
            return
        if matches_any_of(message, [
            "is tars a bot?",
            "tars are you a bot?",
        ]):
            msg.reply("Yep.")
            return
        if matches_any_of(message, [
            "is tars a person?",
            "tars are you a person?",
        ]):
            msg.reply("Nope. I'm a bot.")
            return
        # everything else is returned, so this only happens if no matches
        if cmd.command:
            msg.reply("That's not a command.")

def strip(string):
    return ''.join(l for l in string if l.isalnum()).lower()

def matches_any_of(subject, matches, threshold=80):
    for match in matches:
        if fuzz.ratio(subject.lower(), match) >= threshold:
            return True
    return False
