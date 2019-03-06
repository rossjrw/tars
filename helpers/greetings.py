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
