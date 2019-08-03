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
    user = None
    channel = None
    model = None
    size = 3
    @classmethod
    def command(cls, irc_c, msg, cmd):
        channel = msg.channel
        user = None
        # root has 1 num, 1 string, 1 string startswith #
        for arg in cmd.args['root']:
            if isint(arg): size = arg
            elif arg.startswith('#'): channel = arg
            else: user = arg
        # Run a check to see if we need to reevaluate the model or not
        if cls.channel == channel and cls.user == user:
            model = cls.model
            print("Reusing Markov model")
        else:
            cls.channel = channel
            cls.user = user
            if user == CONFIG.nick:
                msg.reply("blah blah beep boop bot stuff")
                return
            messages = DB.get_messages(channel, user)
            if len(messages) == 0:
                msg.reply("I don't remember {} ever saying anything in {}."
                          .format(user, channel))
                return
            model = cls.make_model(messages)
            cls.model = model
        try:
            sentence = model.make_sentence(tries=1000, force_result=False)
            print("SIZE IS 3")
            if sentence is None:
                # try again with a smaller state size
                # this should only happen with small data sets so I'm not
                #   too concerned about performance
                messages = DB.get_messages(channel, user)
                for decr in range(1, cls.size+1):
                    model = cls.make_model(messages, decrement=decr)
                    sentence = model.make_sentence(tries=1000, force_result=False)
                    print("SIZE IS {}".format(cls.size-decr))
                    if sentence is not None:
                        break
        except AttributeError:
            msg.reply("Looks like {} spoken enough in {} just yet.{}".format(
                ("you haven't" if user == msg.sender else "nobody has" if user
                 is None else "{} hasn't".format(user)),
                channel,
                " ({} messages)".format(len(model.to_dict()['parsed_sentences']))
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
