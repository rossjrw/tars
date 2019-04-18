# Not a plugin
# Provides generic text for shit

from random import choice
import re

def greet(subject):
    user = [
        "Hey, {}.",
        "Howdy, {}.",
        "Hi, {}.",
        "👉😎👉",
    ]
    channel = [
        "Hey everyone.",
        "Great, looks like everyone's here.",
        "This is my favourite channel.",
        "This is my least favourite channel.",
        "Of all the channels I'm in, this is the only one I 'put up' with.",
        "Ah, {}. Good to see you."
    ]
    if subject[0] == "#":
        return choice(channel).format(subject)
    else:
        return choice(user).format(subject)

def bad_command(**kwargs):
    response = [
        "I'm sorry, I didn't quite catch that.",
        "That's not a valid command.",
        "I don't know how to do that.",
        "Are you sure you typed the right thing?",
        "I don't know what that means.",
        "That's not a command.",
        "Bad command, sorry.",
    ]
    message = kwargs['message'] if 'message' in kwargs else choice(response)
    link = " See https://git.io/TARShelp for a list of commands."
    return message + link

def isGreeting(message):
    greetings = [
        "hello", "hi", "howdy", "yo"
    ]
    return 0

def kill_bye():
    responses = [
        "Ok :(",
        "I don't wanna go :(",
        "Finally.",
    ]
    return choice(responses)

def acronym():
    responses = [
        "!Tool-!Assisted !Robotic !Sassmouth",
        "!TARS: !A !Recursive !Semantic",
        "!Totally !Awesome !Robot (/!S)",
        "!Tantalising !And !Rambunctious !Sexbot",
        "ano!Ther bot that !Also helps io do p!Romotion !Stuff",
        "!Target !Attack !Radar !System",
        "!This's !A !Random !Sentence",
        "!Tell !Aaron !Rocks !Suck",
        "!There's !A !Rong !Spelling",
        "!This !Asshole !Robot !Sucks",
        "!Try !And !Rate !SCPs",
        "!These !Acronyms !Really !Suck",
    ]
    return re.sub(r"!([TARS])","\x02\\1\x0F",choice(responses))
