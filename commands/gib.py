""" gib.py

Gib gab gibber gob!
"""

import random
import re

from emoji import emojize
import markovify

from helpers.command import Command, regex_type
from helpers.config import CONFIG
from helpers.database import DB
from helpers.defer import defer
from helpers.error import CommandError, MyFaultError, isint

_URL_PATT = (
    r"https?:\/\/(www\.)?"
    r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}"
    r"\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
)
_YT_PATT = re.compile(r"^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+")
_IMG_PATT = re.compile(r"(imgur)|(((jpeg)|(jpg)|(png)|(gif)))$")


class MarkovFromList(markovify.Text):
    def sentence_split(self, text):
        return [text]


class Gib(Command):
    """Generate a sentence.

    TARS will take all of the messages in the channel and employ an
    extremely sophisticated machine-learning algorithm backed by over $8
    billion in research funding to contribute to the conversation. The result
    will be scarily accurate. Viewer discretion is advised.

    Additionally, any pings (username mentions) that are produced in the
    output will be censored to avoid annoying anyone not present in the
    conversation. To add a nick to the list of pings to search, see
    @command(alias).

    TARS keeps a list of all gibs it's made. It will never make the same gib
    twice. It will also never make a gib that's identical to an existing
    message.

    @example(.gib -u Croquembouche)(make a sentence only using messages spoken
    by Croquembouche.)

    @example(.gib -u Croquembouche TARS -x moo -l 200 -s 2)(make a sentence
    only using messages spoken by Croquembouche or TARS which contain the word
    "moo", that's at least 200 characters long, with a coherency of 2.)
    """

    command_name = "gib"
    defers_to = ["jarvis"]
    arguments = [
        dict(
            flags=['--user', '-u'],
            type=str,
            nargs='+',
            help="""Filter source messages by user(s).

            If not provided, defaults to all users. Add a hyphen to the start
            of the user's name to exclude them but include everyone else.
            """,
        ),
        dict(
            flags=['--channel', '-c'],
            type=regex_type(r"^#", "must be a channel"),
            nargs='+',
            help="""Filter source messages by channel.

            If not provided, defaults to the current channel. To add a channel
            to the filter, both yourself and TARS must be present in it.
            """,
        ),
        dict(
            flags=['--regex', '-x'],
            type=str,
            nargs='+',
            help="""Filter source messages by regex match.""",
        ),
        dict(
            flags=['--me'],
            type=bool,
            help="""Only gib from `/me`-style messages.""",
        ),
        dict(
            flags=['--size', '-s'],
            type=int,
            nargs=None,
            help="""Adjust the coherency of the output.

            'size' refers to the internal state size of the Markov chain. The
            default value is 3. Smaller values produce more nonsensical
            output. Larger values produce more readable output, at the cost of
            longer processing time and maybe being a bit dull.
            """,
        ),
        dict(
            flags=['--no-cache', '-n'],
            type=bool,
            help="""Ignore the Markov model and gib history caches.

            Normally, TARS caches the expensive @command(gib) calculations, and
            will only generate a new Markov model if a non-identical
            @command(gib) is issued (e.g. from a different channel or searching
            a different user). Additionally, TARS keeps a list of output
            sentences and will never generate the same sentence twice. Applying
            @argument(--no-cache) will ignore both of these constraints.
            """,
        ),
        dict(
            flags=['--roulette', '-r'],
            type=str,
            nargs=None,
            choices=['image', 'youtube'],
            help="""Enables roulette mode!

            Instead of generating a nonsensical sentence, TARS will instead
            pick a random link. Either image or youtube links are supported.
            """,
        ),
    ]

    users = []
    channels = []
    model = None
    size = 3
    ATTEMPT_LIMIT = 20
    nocache = False

    def execute(self, irc_c, msg, cmd):
        users = []
        # root has 1 num, 1 string, 1 string startswith #
        if 'channel' in self:
            channels = self['channel']
        elif msg.raw_channel is None:
            raise CommandError(
                "Specify a channel to gib from with --channel/-c"
            )
        else:
            channels = [msg.raw_channel]
        if 'user' in self:
            users = self['user']
        if 'size' in self:
            Gib.size = self['size']
        else:
            Gib.size = 3
        # ignore gib cache?
        if self['no_cache']:
            Gib.nocache = True
        else:
            Gib.nocache = False
        if 'limit' in self:
            limit = self['limit']
        else:
            limit = CONFIG['gib']['limit']
            if not limit:
                limit = 5000
        if 'roulette' in self:
            if len(self['roulette']) == 0:
                raise CommandError(
                    "When using roulette mode, you must "
                    "specify a roulette type"
                )
            roulette_type = self['roulette'][0]
            if roulette_type not in ['video', 'image', 'youtube', 'yt']:
                raise CommandError(
                    "The roulette type must be either "
                    "'image' or one of 'video','youtube','yt'"
                )
            limit = None
        # can only gib a channel both the user and the bot are in
        for channel in channels:
            if channel is msg.raw_channel:
                continue
            if (
                msg.raw_channel is not None
                and self['channel'][0] != 'all'
                and not all(
                    x in DB.get_channel_members(channel)
                    for x in [msg.sender, CONFIG.nick]
                )
            ):
                raise CommandError(
                    "Both you and the bot must be in a channel "
                    "in order to gib it."
                )
            if (
                msg.raw_channel is not None
                and channel != msg.raw_channel
                and not defer.controller(cmd)
            ):
                raise CommandError(
                    "You can only gib the current channel (or "
                    "any channel from PMs)"
                )
        # Run a check to see if we need to reevaluate the model or not
        if Gib.channels == channels and Gib.users == users and not Gib.nocache:
            print("Reusing Markov model")
        else:
            Gib.model = None
            Gib.channels = channels
            if len(Gib.channels) == 0:
                Gib.channels = [msg.raw_channel]
            Gib.users = users
            if len(Gib.users) == 0:
                Gib.users = [None]
        # are we gibbing or rouletting?
        if 'roulette' in self:
            urls = Gib.roulette(roulette_type)
            msg.reply(
                "{} {} · ({} link{} found)".format(
                    emojize(":game_die:"),
                    random.choice(urls),
                    len(urls),
                    ("s" if len(urls) > 1 else ""),
                )
            )
            return
        if 'regex' in self:
            if len(self['regex']) == 0:
                raise CommandError(
                    "When using the regex filter, you must specify a regex"
                )
            patterns = self['regex']
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    raise CommandError(
                        "'{}' isn't a valid regular "
                        "expression: {}".format(pattern, e)
                    )
        else:
            patterns = []
        if 'me' in self:
            patterns.append(r"\u0001ACTION ")
        if 'minlength' in self:
            if len(self['minlength']) == 0:
                raise CommandError(
                    "When using the minimum length modifier "
                    "(--length/-l), you must specify a "
                    "minimum length"
                )
            minlength = self['minlength'][0]
            if not isint(minlength):
                raise CommandError(
                    "When using the minimum length modifier "
                    "(--length/-l), the minimum length must be "
                    "an integer"
                )
            minlength = int(minlength)
        else:
            minlength = 0
        # gibbing:
        try:
            sentence = Gib.get_gib_sentence(
                limit=limit, minlength=minlength, patterns=patterns
            )
            if sentence is None:
                raise AttributeError
        except (RuntimeError, AttributeError):
            raise MyFaultError(
                "Looks like {} spoken enough in {} just yet.{}".format(
                    (
                        "you haven't"
                        if msg.sender in users and len(users) == 1
                        else "nobody has"
                        if len(users) == 0
                        else "{} hasn't".format(users[0])
                        if len(users) == 1
                        else "they haven't"
                    ),
                    (
                        channels[0]
                        if len(channels) == 1
                        and channels[0] == msg.raw_channel
                        else "that channel"
                        if len(channels) == 1
                        else "those channels"
                    ),
                    " ({} messages)".format(
                        len(Gib.model.to_dict()['parsed_sentences'])
                        if Gib.model is not None
                        else 0
                    ),
                )
            )
        # first: remove a ping at the beginning of the sentence
        pattern = r"^(\S+[:,]\s+)(.*)$"
        match = re.match(pattern, sentence)
        if match:
            sentence = match.group(2).strip()
        # second: modify any words that match the names of channel members
        sentence = Gib.obfuscate(
            sentence, DB.get_channel_members(msg.raw_channel)
        )
        # match any unmatched pairs
        sentence = Gib.bracketify(
            sentence, (r"\"\b", "\""), (r"\b[.!?]*\"", "\"")
        )
        sentence = Gib.bracketify(sentence, (r"`\b", "`"), (r"\b[.!?]*`", "`"))
        sentence = Gib.bracketify(sentence, (r"\(", "("), (r"\)", ")"))
        sentence = Gib.bracketify(sentence, (r"\[", "["), (r"\}", "]"))
        sentence = Gib.bracketify(sentence, (r"\{", "{"), (r"\}", "}"))

        cmd.command = cmd.command.lower()
        if "oo" in cmd.command:
            sentence = re.sub(r"[aeiou]", "oob", sentence)
        elif "o" in cmd.command:
            sentence = re.sub(r"[aeiou]", "ob", sentence)
        if cmd.command.startswith("b") and cmd.command.endswith("g"):
            sentence = sentence.upper()
        msg.reply(sentence)

    @staticmethod
    def bracketify(string, opening, closing):
        """Return the given string with balanced brackets.

        Both `opening` and `closing` should be a tuple. The first element
        should be what bracket is being searched for as a regex string. The
        second element should be what that bracket actually is, as a regular
        string.
        """
        opening_find, opening_bracket = opening
        closing_find, closing_bracket = closing
        depths = [0] * len(string)
        for match in re.finditer(opening_find, string):
            for index in range(match.span()[1], len(depths)):
                depths[index] += 1
        for match in re.finditer(closing_find, string):
            for index in range(match.span()[0], len(depths)):
                depths[index] += -1
        string = opening_bracket * -min(depths) + string
        string += closing_bracket * depths[-1]
        return string

    @classmethod
    def get_gib_sentence(
        cls, attempts=0, limit=7500, minlength=0, patterns=None
    ):
        print("Getting a gib sentence")
        # messages = []
        # for channel in cls.channels:
        #     print("Iterating channels")
        #     for user in cls.users:
        #         print("Iterating users")
        #         messages.extend(DB.get_messages(channel, user))
        messages = DB.get_messages(
            Gib.channels,
            minlength=40,
            limit=limit,
            senders=None if Gib.users == [None] else Gib.users,
            patterns=patterns,
        )
        print("messages found: {}".format(len(messages)))
        if len(messages) == 0:
            raise AttributeError
        for decr in range(0, Gib.size):
            print(
                "Making model from messages, size {}".format(Gib.size - decr)
            )
            Gib.model = Gib.make_model(messages, decrement=decr)
            print("Making sentence")
            sentence = Gib.model.make_short_sentence(
                400, minlength, tries=200, force_result=False
            )
            if sentence is not None:
                break
            print("Sentence is None")
        if not Gib.nocache and sentence in DB.get_gibs():
            print(
                "Sentence already sent, {} attempts remaining".format(
                    Gib.ATTEMPT_LIMIT - attempts
                )
            )
            try:
                if attempts < Gib.ATTEMPT_LIMIT:
                    sentence = Gib.get_gib_sentence(
                        attempts + 1, limit, minlength, patterns
                    )
                else:
                    raise RecursionError
            except RecursionError:
                raise MyFaultError(
                    "I didn't find any gibs for that selection "
                    "that haven't already been said."
                )
        if sentence is not None:
            DB.add_gib(sentence)
        return sentence

    @classmethod
    def make_model(cls, messages, decrement=0):
        size = Gib.size - decrement
        if size == 0:
            return None
        else:
            return MarkovFromList(messages, well_formed=False, state_size=size)

    @staticmethod
    def obfuscate(sentence, nicks):
        """Removes pings from a sentence. """
        # Escape regex-active characters
        nicks = [re.escape(nick) for nick in nicks]
        # Always obfuscate "ops", no matter what
        nicks.append("ops")
        nicks = re.compile(
            r"\b" + r"\b|\b".join(nicks) + r"\b", flags=re.IGNORECASE
        )
        # If the channel is None (PM), then the only ping is "ops"
        # If this were not the case, then the nicks regex would be an empty
        # string, which would match and therefore obfuscate all words
        return nicks.sub(Gib.obfuscate_word, sentence)

    @classmethod
    def obfuscate_word(cls, match):
        """Obfuscates a single word to remove a ping."""
        word = list(match.group(0))
        for index, letter in enumerate(word):
            if letter in "aeiouAEIOU":
                word[index] = "*"
                break
        else:
            word.insert(2, "*")
        return "".join(word)

    @classmethod
    def roulette(cls, roulette_type):
        """Get a random image or video link"""
        # take all the messages in the channel, filtered for links
        messages = DB.get_messages(
            Gib.channels, senders=Gib.users, patterns=[_URL_PATT]
        )
        if len(messages) == 0:
            raise MyFaultError(
                "I didn't find any URLs in the selection criteria."
            )
        # then reduce strings containing urls to urls
        urls = [
            re.search(_URL_PATT, message, re.IGNORECASE).group(0)
            for message in messages
        ]
        # make urls unique
        urls = list(set(urls))
        # then filter by either images or videos
        if roulette_type == 'image':
            urls = [url for url in urls if _IMG_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any images.")
        if roulette_type in ['video', 'youtube', 'yt']:
            urls = [url for url in urls if _YT_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any video links.")
        return urls
