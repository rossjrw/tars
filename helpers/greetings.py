# Not a plugin
# Provides generic text for shit

from random import choice

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

def badCommand(cmd):
    response = [
        "I'm sorry, I didn't quite catch that.",
        "That's not a valid command.",
        "I don't know how to do that.",
        "Are you sure you typed the right thing?",
        "I don't know what that means.",
        "That's not a command.",
        "Bad command, sorry.",
    ]
    link = " See https://git.io/TARShelp for a list of commands."
    return choice(response) + link

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
