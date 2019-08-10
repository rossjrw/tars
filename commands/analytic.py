""" analytic.py

Commands for analyising stuff.
"""

from helpers.api import WikidotAPI
from commands.prop import chunks
import numpy
import math
from pprint import pprint
import csv
from helpers.error import CommandError, isint
import markovify
from helpers.database import DB
import re
from helpers.config import CONFIG

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
    sentences = []
    ATTEMPT_LIMIT = 50
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["no-cache n",
                        "user u author a",
                        "channel c",
                        "size s",
                        "help h"])
        if cmd.hasarg('help'):
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
        if cmd.hasarg('channel'):
            if len(cmd.getarg('channel')) == 0:
                raise CommandError("When using the --channel/-c filter, "
                                   "at least one channel must be specified")
            for channel in cmd.getarg('channel'):
                if not channel.startswith('#'):
                    raise CommandError("Channel names must start with #.")
            channels = cmd.getarg('channel')
        if cmd.hasarg('user'):
            if len(cmd.getarg('user')) == 0:
                raise CommandError("When using the --user/-u filter, "
                                   "at least one user must be specified")
            users = cmd.getarg('user')
        if CONFIG.nick in users:
            msg.reply("blah blah beep boop bot stuff")
            return
        # Run a check to see if we need to reevaluate the model or not
        if cls.channels == channels and cls.users == users \
        and not cmd.hasarg('no-cache'):
            print("Reusing Markov model")
        else:
            cls.model = None
            cls.channels = channels
            if len(cls.channels) == 0: cls.channels = [msg.channel]
            cls.users = users
            if len(cls.users) == 0: cls.users = [None]
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
                " ({} messages)".format(len(cls.model.to_dict()['parsed_sentences']))
            ))
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
        members = re.compile("|".join(members), flags=re.IGNORECASE)
        sentence = members.sub(cls.obfuscate, sentence)
        msg.reply(sentence)

    @classmethod
    def get_gib_sentence(cls, attempts=0):
        # try again with a smaller state size
        # this should only happen with small data sets so I'm not
        #   too concerned about performance
        messages = []
        for channel in cls.channels:
            for user in cls.users:
                messages = DB.get_messages(channel, user)
                if len(messages) == 0 and len(users) <= 1:
                    msg.reply("I don't remember {} ever saying anything in {}."
                              .format(user, channel))
                    return
        for decr in range(0, cls.size):
            cls.model = cls.make_model(messages, decrement=decr)
            sentence = cls.model.make_sentence(tries=1000, force_result=False)
            print("SIZE IS {}".format(cls.size-decr))
            if sentence is not None:
                break
        if sentence in cls.sentences:
            print("{} attempts remaining".format(attempts))
            if attempts < cls.ATTEMPT_LIMIT:
                sentence = cls.get_gib_sentence(attempts+1)
            else:
                sentence = "oh no"
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
