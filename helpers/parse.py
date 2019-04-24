"""parse.py

Provides functions for parsing and formatting stuff into other stuff.
"""

import re
import shlex
import pyaib.util.data as data

def parseprint(message):
    #print("[\x1b[1;32mParser\x1b[0m] " + str(message))
    pass

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
        self.ping = None # identity of the ping
        self.unping = None # raw command without ping
        self.pinged = False # was the ping TARS?
        self.command = None # base command
        self.message = None # varies
        self.quote_error = False # was there a shlex error?
        self.args = None # command arguments as dict w/ subargs as list
        parseprint("Raw input: " + self.raw)

        # Was someone pinged?
        pattern = r"^([A-Za-z0-9\\\[\]\^_-{\|}]+)[!,:\.]+\s*(.*)$"
        match = re.search(pattern, self.raw)
        if match:
            # Remove ping from the message
            self.message = match.group(2).strip()
            self.unping = self.message
            self.ping = match.group(1).strip()
        else:
            self.message = self.raw
            self.unping = self.message

        if isinstance(self.ping, str):
            if self.ping.upper() == "TARS":
                self.pinged = True

        parseprint("After ping extraction: " +
                   "\nping: >{}<".format(self.ping) +
                   "\nmessage: >{}<".format(self.message) +
                   "\npinged: >{}<".format(self.pinged))

        # What was the command?
        # Check for regular commands (including chevron)
        if self.pinged:
            pattern = (r"^(?P<signal>[!,\.\?]{0,2})"
                       r"(?P<cmd>[^!,\.\?\s]+)"
                       r"(?P<rest>.*)$")
        else:
            # Force the command to be marked if we weren't pinged
            pattern = (r"^(?P<signal>[!,\.\?]{1,2})"
                       r"(?P<cmd>[^!,\.\?\s]+)"
                       r"(?P<rest>.*)$")
        match = re.search(pattern, self.message)
        if match:
            # Remove command from the message
            self.command = match.group('cmd').strip().lower()
            try:
                self.message = match.group('rest').strip()
            except IndexError:
                self.message = ""
            parseprint("Doing a " + self.command + "!")
            # if >1 punctuation used, override bot detection later
            if len(match.group('signal')) > 1:
                self.force = True
        else:
            # No command - work out what to do here
            parseprint("No command!")

        # What were the arguments?
        if self.command:
            # remove apostrophes because they'll fuck with shlex
            self.message = self.message.replace("'", "<<APOSTROPHE>>")
            try:
                self.message = shlex.split(self.message, posix=False)
            except ValueError:
                # raised if shlex detects fucked up quotemarks
                self.message = self.message.split()
                self.quote_error = True
            for i,word in enumerate(self.message):
                self.message[i] = word.replace("<<APOSTROPHE>>", "'")
            # arguments is now a list, quotes are preserved
            # need to split it into different lists per tag, though
            self.args = {'root': []}
            currArg = 'root'
            for argument in self.message:
                if argument[:1] == "-" and len(argument) == 2 \
                or argument[:2] == "--" and len(argument) >= 2:
                    currArg = argument.strip("-")
                    self.args[currArg] = []
                else:
                    self.args[currArg].append(argument)
            # empty args exist as a present but empty list
            # detect a chevron command
            pattern = r"^(\^+)$"
            match = re.match(pattern, self.command)
            if match:
                chevs = str(len(self.command))
                self.command = "chevron"
                if 'root' in self.args:
                    self.args['root'].insert(0, chevs)
                else:
                    self.args['root'] = [chevs]
        else:
            # It wasn't a command, so we probably don't need to do anything
            pass

    def hasarg(self, *args):
        """Checks whether this command has a given argument."""
        # args should be ('argument','a')
        for arg in args:
            if arg in self.args:
                return True
        return False

    def getarg(self, *args):
        """Gets the value of a given argument."""
        for arg in args:
            if arg in self.args:
                return self.args[arg]
        raise AttributeError("Command does not have argument(s):"
                             + ", ".join(args))

    def expandargs(self, args):
        """Expand short args to long ones
        Expects one array of "long s" pairs"""
        for pair in args:
            aliases = pair.split()
            # Keep the parent alias for reference
            parent = ""
            for key,alias in enumerate(aliases):
                # ignore the 1st one
                if key == 0:
                    parent = alias
                    continue
                else:
                    if alias in self.args:
                        # Get and delete shorthand property in one swoop
                        self.args[parent] = self.args.pop(alias, None)

# Parse a command
def command(message):
    """Converts a raw IRC message to a command."""
    return ParsedCommand(message)

# Parse a nick to its IRCCloud colour
def nickColor(string):
    length = 27
    colours = [180,220,216,209,208,46,
               11,143,113,77,108,71,79,
               37,80,14,39,117,75,69,146,
               205,170,213,177,13,217]

    def t(x):
        x &= 0xFFFFFFFF
        if x > 0x7FFFFFFF:
            x -= 0x100000000
        return float(x)

    bytes = string.lower()
    bytes = re.sub(r"^#", "", bytes)
    bytes = re.sub(r"[`_]+$", "", bytes)
    bytes = re.sub(r"\|.*$", "", bytes)
    bytes = bytes.encode('utf-16-le')
    hash = 0.0
    for i in range(0, len(bytes), 2):
        char_code = bytes[i] + 256*bytes[i+1]
        hash = char_code + t(int(hash) << 6) + t(int(hash) << 16) - hash
    index = int(hash % length if hash >= 0 else abs(hash % length - length))
    return "\x1b[38;5;{}m{}\x1b[0m".format(colours[index], string)

def output(output):
    """Takes an output message from plugins/log.py"""
    output = str(output)
    pattern = r"(?P<kind>[A-Z]+) (?P<ch>\S+) :(?P<message>.*)"
    match = re.match(pattern, output)
    if not match:
        return None
    msg = {}
    #if match.group('ch')[0] == '#':
    #    msg['channel'] = match.group('ch')
    #else:
    #    msg['channel'] = "private"
    #    msg['nick'] = match.group('ch')
    msg['channel'] = match.group('ch')
    msg['message'] = match.group('message')
    return msg
