import re
import shlex
import pyaib.util.data as data

def parseprint(message):
    print("[\x1b[1;32mParser\x1b[0m] " + str(message))

class ParsedCommand():
    """ParsedCommand

    A dictionary with pings, commands and arguments bundled up nicely.
    .raw - the original message, unchanged
    .ping - nick of the message's ping
    .pinged - bool; was TARS pinged?
    .command - the actual command itself
        .command - the root command
        .arguments - dict with each keys of tags and values as argument
                     tuples. First tuple has tag "root". Tags will be
                     either long or short depending on user input.
    """
    def __init__(self, message):
        # Check that the message is a string
        self.raw = str(message)
        self.ping = False
        self.pinged = False
        self.command = False
        self.message = False
        self.quote_error = False
        self.arguments = False
        parseprint("Raw input: " + self.raw)

        # Was someone pinged?
        pattern = r"^([A-Za-z0-9\\\[\]\^_-{\|}]+)[!,:\.]+\s*(.*)$"
        match = re.search(pattern, self.raw)
        if match:
            # Remove ping from the message
            self.message = match.group(2).strip()
            self.ping = match.group(1).strip()
        else:
            self.message = self.raw

        self.pinged = self.ping == "TARS"
        parseprint("After ping extraction: " +
                   "\nping: {}".format(self.ping) +
                   "\nmessage: {}".format(self.message) +
                   "\npinged: {}".format(self.pinged))

        # What was the command?
        if self.pinged:
            pattern = r"^([!,\.\?\"']*)([\w^]+)(.*)$"
        else:
            # Force the command to be marked if we weren't pinged
            pattern = r"^(?P<signal>[!,\.\?\"']+)(?P<cmd>[\w^]+)(?P<rest>.*)$"
        match = re.search(pattern, self.message)
        if match:
            # Remove command from the message
            self.command = match.group("cmd").strip().lower()
            try:
                self.message = match.group("rest").strip()
            except IndexError:
                self.message = ""
            parseprint("Doing a " + self.command + "!")
            if len(match.group("signal")) > 1:
                self.force = True
        else:
            # No command - work out what to do here
            parseprint("No command!")

        # What were the arguments?
        if self.command:
            # remove apostrophes because they'll fuck with shlex
            self.message = self.message.replace("'", "<<APOSTROPHE>>")
            try:
                self.message = shlex.split(self.message)
            except ValueError:
                # raised if shlex detects fucked up quotemarks
                self.message = self.message.split()
                self.quote_error = True
            for word in self.message:
                word = word.replace("<<APOSTROPHE>>", "'")
            # arguments is now a list, quotes are preserved
            # need to split it into different lists per tag, though
            self.arguments = {}
            currArg = "root"
            for argument in self.message:
                if argument[:1] == "-" and len(argument) == 2 \
                or argument[:2] == "--" and len(argument) >= 2:
                    currArg = argument.strip("-")
                else:
                    # if this tag doesn't exist, make it a list
                    if not currArg in self.arguments:
                        self.arguments[currArg] = []
                    self.arguments[currArg].append(argument)
            # now arguments should be dict of tag: value, w/ root as start
        else:
            # It wasn't a command, so we probably don't need to do anything
            pass

# Parse a command
def command(message):
    """Converts a raw IRC message to a command."""
    return ParsedCommand(message)

# Parse a nick to its IRCCloud colour
def nickColor(nick, length=27):
    """Gets the IRCCloud colour of a given nick."""
    colours = [180,220,216,209,208,46,
               11,143,113,77,108,71,79,
               37,80,14,39,117,75,69,146,
               205,170,213,177,13,217]

    def t(x):
        # if x>0xFFFFFFFF:
        x = x & 0xFFFFFFFF
        if x>0x7FFFFFFF:
            # x = -(0x100000000-x)
            # x = x ^ 0xFFFFFFFF
            # x = ~x
            x = -0x80000000 + x
        return x

    # Copied from IRCCloud's formatter.js
    old_nick = nick
    nick = nick.lower()
    nick = re.sub(r"[`_]+$", "", nick)
    nick = re.sub(r"\|.*$", "", nick)
    hash = t(0)
    for i,letter in enumerate(nick):
        # print(t(hash), t(hash << 6), t(hash << 16))
        hash = t(hash)
        hash = t(t(ord(letter)) + t(hash << 6) + t(hash << 16) - t(hash))
        # print(bin(hash), hash, ord(letter))
    index = hash % length
    return "\x1b[38;5;{}m{}\x1b[0m".format(colours[index], old_nick)
