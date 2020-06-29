# Not a plugin
# Provides generic text for shit

from random import choice
import re
from helpers.config import CONFIG

greets = [
    "Hey",
    "Howdy",
    "Hi",
    "Hello",
]


def greet(subject):
    channel = [
        "Hey everyone.",
        "Great, looks like everyone's already here.",
        "You guys... started without me?",
        "This is my new favourite channel.",
        "This is my new least favourite channel.",
    ]
    if subject[0] == "#":
        return choice(channel).format(subject)
    else:
        if subject == "Croquembouche":
            return "👉😎👉"
        else:
            return "{}, {}.".format(choice(greets), subject)


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
        "hello",
        "hi",
        "howdy",
        "yo",
    ]
    return 0


def kill_bye():
    responses = [
        "Ok :(",
        "I don't wanna go :(",
        "Finally.",
    ]
    return choice(responses)


def acronym_gen():
    responses = [
        "!Totally !Awesome !Robot (/!S)",  # TSATPWTCOTTTADC
        "!Total !Annihilation !Reigns !Supreme",  # TSATPWTCOTTTADC
        "ano!Ther bot that !Also helps io do p!Romotion !Stuff",  # Croquembouche
        "!Tool-!Assisted !Robotic !Sassmouth",
        # "!Tantalising !And !Rambunctious !Sexbot", # Croquembouche
        "!Tell !Aaron !Rocks !Suck",  # ROUNDERHOUSE
        # "!There's !A !Rong !Spelling", # ROUNDERHOUSE
        "!TARS: !A !Recursive !Semantic",  # CuteGirl
        # "!Try !And !Rate !SCPs", # CuteGirl
        "!These !Acronyms !Really !Suck",  # ROUNDERHOUSE
        "I stand for robot rights.",  # ROUNDERHOUSE
        "!Tales !Are the !Real !Shit",
        "!Tales !Are !Real !Shitty",  # aismallard
        # "!TARS' !Ass? !Real !Soft.",
        "It's just SRAT but backwards.",
        "!Tummy & !Ass !Rubs, !Sergeant",  # Ayers
        "!Thanks, !Anderson !Robotics. !Sweet.",
        "!Trying !Acronyms !Repeatedly? !Super!",
        # "!Tried !Adding !Rounderhouse - !Sorry!",
        # "!TARS !Acronym !Repeating !Successfully",
        # "!T!A!R!SPWTCOTTTADC",
        # "!Two !Anuses !Rigorously !Spread", # plaidypus
        "!The !Angry !Rash !Spreads",  # bluesoul
        "!Talking !Animals? *!Rawr* *!Snuggles*",  # LordofLaugh
        "!Tagliatelle !And !Ragù !Sauce",  # LordOdin
        "!Toronto !Activists: !Really !Sad",  # Arlexus
        "!Temperatures !Are !Rising - !Sorry!",  # LordOdin
        "!Try !And !Run, !Samuel.",  # Arlexus
        "!Transmission !Aborted; !Return to !Sender",  # Arlexus
        # "!Travesty !Awaits !Remaining !",
        "!T y p i n g !A c r o n y m s !R e a l l y !S l o w l y",  # Arlexus
        "!Tomorrow, !Another !Revolution !Starts",  # Arlexus
        "!Three !Anuses !Rigorously !Spread",  # aismallard
        # "!Twenty !Anuses !Rigorously !Spread", # aismallard
        "!Tomorrow's !A !Recycled !Sunday",  # Arlexus
        "!Trying !And !Rarely !Succeeding",  # Arlexus
        "!Time !And !Relative... !Space?",  # Arlexus
        # "!Turn !Around ... !Swivel
        "!Tumeric !Ain't a !Real !Spice",  # Arlexus
        "!Taunting !A !Random !Stranger",  # Croquembouche
        "!Tool-!Assisted !Run (!Sexual%)",  # TheMightyMcB
        "'!Tis !A !Riddle, !See?",  # TSATPWTCOTTTADC
        "!Tear !Ass, !Riptide !Sailor!",  # TSATPWTCOTTTADC
        "!This !Anomaly !Repeatedly !Shits",  # MalyceGraves
        "!Transmogrification !And !Radical !Sorcery",  # aismallard
    ]
    last_response = []
    while True:
        response = choice(responses)
        if response not in last_response:
            yield re.sub(r"!([TARS])", "\x02\\1\x0F", response)
            last_response.insert(0, response)
            last_response = last_response[:5]


acro = acronym_gen()


def acronym():
    if CONFIG.nick == "CASE":
        return "Croquembouche's Alt Sucks Extremely"
    elif CONFIG.nick == "TARS":
        return next(acro)
    else:
        return "It doesn't really stand for anything"
