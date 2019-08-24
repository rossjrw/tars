""" gib.py

Gib gab gibber gob!
"""

from helpers.api import WikidotAPI
from commands.prop import chunks
import numpy
import math
from pprint import pprint
import csv
from helpers.error import CommandError, MyFaultError, isint
import markovify
from helpers.database import DB
import re
from helpers.config import CONFIG
import random
from emoji import emojize
from helpers.defer import defer

class MarkovFromList(markovify.Text):
    def sentence_split(self, text):
        return [text]

class gib:
    users = []
    channels = []
    model = None
    size = 3
    ATTEMPT_LIMIT = 30
    nocache = False
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["no-cache n",
                        "user u author a",
                        "channel c",
                        "size s",
                        "roulette r",
                        "help h"])
        if 'help' in cmd:
            msg.reply("Usage: .gib [--channel #channel] [--user user] "
                      "[--no-cache]")
            return
        channels = [msg.channel]
        users = []
        # root has 1 num, 1 string, 1 string startswith #
        for arg in cmd.args['root']:
            if arg.startswith('#'):
                raise CommandError("Try .gib -c {}".format(arg))
            else:
                raise CommandError("Try .gib -u {}".format(arg))
        if 'channel' in cmd:
            if len(cmd['channel']) == 0:
                raise CommandError("When using the --channel/-c filter, "
                                   "at least one channel must be specified")
            if cmd['channel'][0] == "all":
                if defer.controller(cmd):
                    channels = DB.get_all_channels()
                    print("ALL CHANNELS",channels)
                    msg.reply("Gibbing from all channels I'm in:")
                else:
                    msg.reply("Gibbing from all channels you're in:")
                    # get all channels this user is in
                    raise MyFaultError("This isn't implemented yet.")
            else:
                for channel in cmd['channel']:
                    if not channel.startswith('#'):
                        raise CommandError("Channel names must start with #.")
                channels = cmd['channel']
        if 'user' in cmd:
            if len(cmd['user']) == 0:
                raise CommandError("When using the --user/-u filter, "
                                   "at least one user must be specified")
            users = cmd['user']
        if 'size' in cmd:
            try:
                cls.size = int(cmd['size'][0])
            except ValueError:
                raise CommandError("Sizes must be numbers")
        else:
            cls.size = 3
        if 'roulette' in cmd:
            if len(cmd['roulette']) == 0:
                raise CommandError("When using roulette mode, you must "
                                   "specify a roulette type")
            roulette_type = cmd['roulette'][0]
            if roulette_type not in ['video','image','youtube','yt']:
                raise CommandError("The roulette type must be either "
                                   "'image' or one of 'video','youtube','yt'")
        # ignore gib cache?
        if 'no-cache' in cmd:
            cls.nocache = True
        else:
            cls.nocache = False
        # can only gib a channel both the user and the bot are in
        for channel in channels:
            if channel is msg.channel:
                continue
            if msg.channel is not None \
               and cmd['channel'][0] != 'all' \
               and not all(x in DB.get_channel_members(channel)
                           for x in [msg.sender, CONFIG.nick]):
                raise CommandError("Both you and the bot must be in a channel "
                                   "in order to gib it.")
            if msg.channel is not None \
               and channel != msg.channel \
               and not defer.controller(cmd):
                raise CommandError("You can only gib the current channel (or "
                                   "any channel from PMs)")
        # Run a check to see if we need to reevaluate the model or not
        if cls.channels == channels and cls.users == users \
           and not cls.nocache:
            print("Reusing Markov model")
        else:
            cls.model = None
            cls.channels = channels
            if len(cls.channels) == 0: cls.channels = [msg.channel]
            cls.users = users
            if len(cls.users) == 0: cls.users = [None]
        # are we gibbing or rouletting?
        if 'roulette' in cmd:
            urls = cls.roulette(roulette_type)
            msg.reply("{} {} · ({} link{} found)"
                      .format(emojize(":game_die:"),
                              random.choice(urls),
                              len(urls),
                              ("s" if len(urls) > 1 else "")))
            return
        # gibbing:
        try:
            sentence = cls.get_gib_sentence()
        except AttributeError:
            msg.reply("Looks like {} spoken enough in {} just yet.{}".format(
                ("you haven't" if msg.sender in users and len(users) == 1
                 else "nobody has" if len(users) == 0
                 else "{} hasn't".format(users[0]) if len(users) == 1
                 else "they haven't"),
                (channels[0] if len(channels) == 1 and channels[0] == msg.channel
                 else "that channel" if len(channels) == 1
                 else "those channels"),
                " ({} messages)".format(
                    len(cls.model.to_dict()['parsed_sentences'])
                    if cls.model is not None
                    else 0)))
            return
        # now we need to remove pings from the sentence
        # first: remove a ping at the beginning of the sentence
        print(sentence)
        pattern = r"^(\S+[:,]\s+)(.*)$"
        match = re.match(pattern, sentence)
        if match:
            sentence = match.group(2).strip()
        # second: modify any words that match the names of channel members
        members = DB.get_channel_members(msg.channel)
        members = re.compile(r"\b" + r"\b|\b".join(members) + r"\b",
                             flags=re.IGNORECASE)
        if msg.channel is not None:
            sentence = members.sub(cls.obfuscate, sentence)
        msg.reply(sentence)

    @classmethod
    def get_gib_sentence(cls, attempts=0):
        print("Getting a gib sentence")
        # try again with a smaller state size
        # this should only happen with small data sets so I'm not
        #   too concerned about performance
        messages = []
        for channel in cls.channels:
            print("Iterating channels")
            for user in cls.users:
                print("Iterating users")
                messages = DB.get_messages(channel, user)
        print("messages found: {}".format(len(messages)))
        if len(messages) == 0:
            raise AttributeError
        for decr in range(0, cls.size):
            print("Making model from messages, size {}".format(cls.size-decr))
            cls.model = cls.make_model(messages, decrement=decr)
            print("Making sentence")
            sentence = cls.model.make_short_sentence(400, tries=200, force_result=False)
            if sentence is not None:
                break
            print("Sentence is None")
        if not cls.nocache and sentence in DB.get_gibs():
            print("Sentence already sent, {} attempts remaining".format(cls.ATTEMPT_LIMIT-attempts))
            try:
                if attempts < cls.ATTEMPT_LIMIT:
                    sentence = cls.get_gib_sentence(attempts+1)
                else:
                    raise RecursionError
            except RecursionError:
                raise MyFaultError("I didn't find any gibs for that selection "
                                   "that haven't already been said.")
        if sentence is not None:
            DB.add_gib(sentence)
        return sentence

    @classmethod
    def make_model(cls, messages, decrement=0):
        size = cls.size - decrement
        if size == 0:
            return None
        else:
            return MarkovFromList(messages, well_formed=False, state_size=size)

    @classmethod
    def obfuscate(cls, match):
        word = list(match.group(0))
        for index,letter in enumerate(word):
            if letter in "aeiouAEIOU":
                word[index] = "*"
                break
        else:
            word.insert(2, "*")
        return ''.join(word)

    @classmethod
    def roulette(cls, roulette_type):
        """Get a random image or video link"""
        # take all the messages in the channel, filtered for links
        messages = []
        for channel in cls.channels:
            for user in cls.users:
                messages = DB.get_messages(channel, user, _URL_PATT)
                if len(messages) == 0 and len(cls.users) <= 1:
                    raise MyFaultError("I didn't find any URLs in the "
                                       "selection criteria.")
        # then reduce strings containing urls to urls
        urls = [re.search(_URL_PATT, message).group(0) for message in messages]
        # make urls unique
        urls = list(set(urls))
        # then filter by either images or videos
        if roulette_type == 'image':
            urls = [url for url in urls if _IMG_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any images.")
        if roulette_type in ['video','youtube','yt']:
            urls = [url for url in urls if _YT_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any video links.")
        return urls