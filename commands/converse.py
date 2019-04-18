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
        message = msg.message
        if matches_any_of(message, [
            "what does tars stand for?",
            "is tars an acronym?",
        ]):
            msg.reply(acronym())
        if matches_any_of(message, [
            "is tars a bot?",
            "tars are you a bot?",
        ]):
            msg.reply("Yep.")
        if matches_any_of(message, [
            "is tars a person?",
            "tars are you a person?",
        ]):
            msg.reply("Nope. I'm a bot.")

def strip(string):
    return ''.join(l for l in string if l.isalnum()).lower()

def matches_any_of(subject, matches, threshold=80):
    for match in matches:
        if fuzz.partial_ratio(subject.lower(), match) >= threshold:
            return True
    return False
