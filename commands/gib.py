""" gib.py

Gib gab gibber gob!
"""

import random
import re

from emoji import emojize
import markovify

from helpers.basecommand import Command, matches_regex, regex_type
from helpers.config import CONFIG
from helpers.database import DB
from helpers.defer import defer
from helpers.error import CommandError, MyFaultError

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
    conversation. To add your nick to the list of pings to remove, see
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
            flags=['--user', '-u', '--author', '-a'],
            type=str,
            nargs='+',
            help="""Filter source messages by user(s).

            Only messages said by the named users will be used to construct the
            gib. If not provided, defaults to all users. Add a hyphen to the
            start of the user's name to exclude them but include everyone else.
            """,
        ),
        dict(
            flags=['--channel', '--ch', '-c'],
            type=matches_regex(r"^#", "must be a channel"),
            nargs='+',
            help="""Filter source messages by channel.

            If not provided, defaults to the current channel. To add a channel
            to the filter, both yourself and TARS must be present in it. You
            can only choose which channels to gib from if you are gibbing in
            PMs with the bot; otherwise, you can only gib from the current
            channel.
            """,
        ),
        dict(
            flags=['--regex', '-x'],
            type=regex_type,
            nargs='+',
            help="""Filter source messages by regex match.

            Only messages that match the provided regular expression will be
            used to construct the gib. Can be used for simple word matches,
            e.g. @example(.gib -x hello).
            """,
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
            default=3,
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
            flags=['--media', '-m'],
            type=str,
            nargs=None,
            choices=['image', 'youtube'],
            help="""Picks a random image or YouTube link instead of gibbing.

            Instead of generating a nonsensical sentence, TARS will instead
            pick a random link. Either image or YouTube links are supported.
            """,
        ),
        dict(
            flags=['--minlength', '-l'],
            type=int,
            nargs=None,
            default=0,
            help="""The minimum length (characters) for the gib.

            If the gib process generates a gib shorter than this amount, it is
            discarded and another one is generated.

            Gibs that fail for being too short contribute to the attempt limit.
            Very long minimum lengths will nearly always fail.
            """,
        ),
        dict(
            flags=['--limit'],
            type=int,
            nargs=None,
            default=CONFIG['gib']['limit'] or 5000,
            help="""The message selection size limit.

            Limits the number of messages that can be in the gib selection.
            Defaults to {}.
            """.format(
                CONFIG['gib']['message_limit'] or 5000
            ),
        ),
    ]

    cache = {
        'model': None,
        'users': [],
        'channels': [],
        'size': 3,
        'limit': 0,
    }

    def execute(self, irc_c, msg, cmd):
        self['channel'] = self['channel']
        if len(self['channel']) == 0:
            if msg.raw_channel is None:
                # Happens when gibbing from PMs
                raise CommandError(
                    "Specify a channel to gib from with --channel/-c"
                )
            # Default channel is the current one
            self['channel'] = [msg.raw_channel]
        limit = self['limit'] or CONFIG['gib']['message_limit'] or 5000
        if 'media' in self:
            limit = -1
        if 'me' in self:
            self['regex'].append(re.compile(r"^\u0001ACTION "))
        # can only gib a channel both the user and the bot are in
        for channel in self['channel']:
            if channel == msg.raw_channel:
                continue
            if (
                msg.raw_channel is not None
                and self['channel'][0] != 'all'
                and not all(
                    nick in DB.get_channel_members(channel)
                    for nick in [msg.sender, CONFIG.nick]
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
        # Does the model need to be regenerated?
        if not self['nocache'] and all(
            Gib.cache['model'] is not None,
            Gib.cache['channels'] == self['channel'],
            Gib.cache['users'] == self['user'],
            Gib.cache['size'] == self['size'],
            Gib.cache['limit'] == limit,
        ):
            print("Reusing Markov model")
        else:
            Gib.cache['model'] = None
            Gib.cache['channels'] = self['channel']
            Gib.cache['users'] = self['user']
            Gib.cache['size'] = self['size']
            Gib.cache['limit'] = limit
        # are we gibbing or rouletting?
        if 'media' in self:
            urls = self.media_roulette()
            msg.reply(
                "{} {} · ({} link{} found)".format(
                    emojize(":game_die:"),
                    random.choice(urls),
                    len(urls),
                    "s" if len(urls) > 1 else "",
                )
            )
            return
        # gibbing:
        try:
            sentence = self.get_gib_sentence(limit=limit)
            if sentence is None:
                raise AttributeError
        except (RuntimeError, AttributeError) as error:
            raise MyFaultError(
                "Looks like {} spoken enough in {} just yet.{}".format(
                    (
                        "you haven't"
                        if msg.sender in self['user']
                        and len(self['user']) == 1
                        else "nobody has"
                        if len(self['user']) == 0
                        else "{} hasn't".format(self['user'][0])
                        if len(self['user']) == 1
                        else "they haven't"
                    ),
                    (
                        self['channel'][0]
                        if (
                            len(self['channel']) == 1
                            and self['channel'][0] == msg.raw_channel
                        )
                        else "that channel"
                        if len(self['channel']) == 1
                        else "those channels"
                    ),
                    " ({} messages)".format(
                        len(Gib.cache['model'].to_dict()['parsed_sentences'])
                        if Gib.cache['model'] is not None
                        else 0
                    ),
                )
            ) from error
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
        sentence = Gib.bracketify(sentence, ("“", "“"), (r"”", "”"))
        sentence = Gib.bracketify(sentence, ("‘", "‘"), (r"’", "’"))
        sentence = Gib.bracketify(sentence, ("«", "«"), (r"»", "»"))

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

    def get_gib_sentence(self, attempts=0, limit=7500):
        print("Getting a gib sentence")
        # messages = []
        # for channel in cls.channels:
        #     print("Iterating channels")
        #     for user in cls.users:
        #         print("Iterating users")
        #         messages.extend(DB.get_messages(channel, user))
        messages = DB.get_messages(
            self['channel'],
            minlength=40,
            limit=limit,
            senders=None if self['user'] == [] else self['user'],
            patterns=self['regex'],
        )
        print("messages found: {}".format(len(messages)))
        if len(messages) == 0:
            raise AttributeError
        # Automatically decrement the state size if the higher state size fails
        for decr in range(0, self['size']):
            print(
                "Making model from messages, size {}".format(
                    self['size'] - decr
                )
            )
            # The model cache depends on the state size, so if there is a state
            # size decrement, discard it anyway
            if decr != 0:
                Gib.cache['model'] = None
            model = (
                Gib.cache['model']
                if Gib.cache['model'] is not None
                else Gib.make_model(messages, self['size'], decrement=decr)
            )
            print("Making sentence")
            sentence = model.make_short_sentence(
                400, self['minlength'], tries=200, force_result=False
            )
            if sentence is not None:
                break
            print("Sentence is None")
        if not self['nocache'] and sentence in DB.get_gibs():
            print(
                "Sentence already sent, {} attempts remaining".format(
                    CONFIG['gib']['attempt_limit'] - attempts
                )
            )
            try:
                if attempts < CONFIG['gib']['attempt_limit']:
                    sentence = self.get_gib_sentence(attempts + 1, limit)
                else:
                    raise RecursionError
            except RecursionError as error:
                raise MyFaultError(
                    "I didn't find any gibs for that selection "
                    "that haven't already been said."
                ) from error
        if sentence is not None:
            DB.add_gib(sentence)
        return sentence

    @staticmethod
    def make_model(messages, base_size, decrement=0):
        """Generate the Markov model."""
        size = base_size - decrement
        if size == 0:
            return None
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

    @staticmethod
    def obfuscate_word(match):
        """Obfuscates a single word to remove a ping."""
        word = list(match.group(0))
        for index, letter in enumerate(word):
            if letter in "aeiouAEIOU":
                word[index] = "*"
                break
        else:
            word.insert(2, "*")
        return "".join(word)

    def media_roulette(self):
        """Get a random image or video link."""
        # take all the messages in the channel, filtered for links
        messages = DB.get_messages(
            self['channel'], senders=self['user'], patterns=[_URL_PATT]
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
        if self['media'] == 'image':
            urls = [url for url in urls if _IMG_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any images.")
        if self['media'] == 'youtube':
            urls = [url for url in urls if _YT_PATT.search(url)]
            if len(urls) == 0:
                raise MyFaultError("I didn't find any video links.")
        return urls
