""" analytic.py

Commands for analyising stuff.
"""

from helpers.api import WikidotAPI
from commands.prop import chunks
import numpy
import math
from pprint import pprint
import csv
from helpers.error import CommandError
import markovify

class analyse_wiki:
    """For compiling data of the file contents of a sandbox"""
    @classmethod
    def command(cls, irc_c, msg, cmd):
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
    @classmethod
    def command(cls, irc_c, msg, cmd):
        channel = None
        user = None
        if len(cmd.args['root']) >= 1:
            if cmd.args['root'][0].startswith('#'):
                channel = cmd.args['root'][0]
            else:
                user = cmd.args['root'][0]
        if len(cmd.args['root']) >= 2:
            if cmd.args['root'][1].startswith('#'):
                channel = cmd.args['root'][1]
            else:
                user = cmd.args['root'][1]
        if channel is None:
            channel = msg.channel
        if cls.channel == channel and cls.user == user:
            model = cls.model
            print("Reusing Markov model")
        else:
            cls.channel = channel
            cls.user = user
            model = MarkovFromList(
                irc_c.db._driver.get_messages(channel, user),
                well_formed=False,
                state_size=1
            )
            cls.model = model
        msg.reply(model.make_sentence(tries=100))
