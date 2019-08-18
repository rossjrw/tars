""" analytic.py

Commands for analyising stuff.
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

_URL_PATT = (r"https?:\/\/(www\.)?"
                r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}"
                r"\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
_YT_PATT = re.compile(r"^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+")
_IMG_PATT = re.compile(r"(imgur)|(((jpeg)|(jpg)|(png)|(gif)))$")

class analyse_wiki:
    """For compiling data of the file contents of a sandbox"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if not defer.controller(cmd):
            raise CommandError("I'm afriad I can't let you do that.")
            return
        if len(cmd.args['root']) < 1:
            raise CommandError("Must specify the wiki to analyse")
        if len(cmd.args['root']) == 2:
            abort_limit = int(cmd.args['root'][1])
        else:
            abort_limit = -1
        if msg.sender != 'Croquembouche':
            msg.reply("Only Croquembouche can do that, sorry!")
            return
        target = WikidotAPI(cmd.args['root'][0])
        msg.reply("Fetching data from {}...".format(cmd.args['root'][0]))
        # 1. get a list of all pages
        # 2. get the filenames associated with those pages
        # 3. get the file metas associated with those files
        # 4. save everything to a spreadsheet (csv would be fine)
        # ---
        # 1. get a list of all pages
        pages = target.select({})
        msg.reply("I found {} pages.".format(len(pages)))
        msg.reply("Getting file names...")
        # pages is now a list of page names
        # make a list for files
        files_list = [] # this is the master list
        percents = [math.ceil(i*len(pages)) for i in numpy.linspace(0, 1, 101)]
        # get select_files per 1 page
        for i,page in enumerate(pages):
            if i in percents:
                msg.reply("{}% complete".format(percents.index(i)))
            try:
                pages[i] = {'page': page, 'files': target.select_files({'page': page})}
            except Exception as e:
                msg.reply("Error on {}: {}".format(page['page'],str(e)))
            print("Found {} files for {}".format(len(pages[i]['files']),page))
            if i == abort_limit:
                msg.reply("Process aborted after {} pages".format(abort_limit))
                break
        # TODO loop over pages and remove errored entries
        msg.reply("Getting info for files...")
        for i,page in enumerate(pages):
            if i in percents:
                msg.reply("{}% complete".format(percents.index(i)))
            # for each page, get_files_meta can take up to 10 files
            # no problem for 10 or less files - what to do when there's more?
            # chunks the file into 10s but then we need to get the index?
            # or do we
            for files in chunks(page['files'], 10):
                print(files)
                try:
                    f = target.get_files_meta({'page': page['page'],
                                               'files': files})
                    pprint(f)
                    for filename in files:
                        f[filename]['page'] = page['page']
                        files_list.append(f[filename])
                except Exception as e:
                    msg.reply("Error on {} of {}: {}".format(files,page['page'],str(e)))
            if i == abort_limit:
                msg.reply("Process aborted after {} pages".format(abort_limit))
                break
        msg.reply("List of files created.")
        msg.reply("Outputting to .csv...")
        with open("wiki_analysis.csv",'w') as f:
            w = csv.DictWriter(f, files_list[0].keys())
            w.writeheader()
            w.writerows(files_list)
        msg.reply("Done.")

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
        # can't gib the bot (yet!)
        if CONFIG.nick.lower() in [user.lower() for user in users]:
            msg.reply("blah blah beep boop bot stuff")
            return
        # can only gib a channel both the user and the bot are in
        for channel in channels:
            if channel is msg.channel:
                continue
            if msg.channel is not None \
               and not all(x in DB.get_channel_members(channel)
                           for x in [msg.sender, CONFIG.nick]):
                raise CommandError("Both you and the bot must be in a channel "
                                   "in order to gib it.")
            if msg.channel is not None and channel != msg.channel:
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
