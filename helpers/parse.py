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
            self.ping = False

        self.pinged = self.ping == "TARS"
        parseprint("After ping extraction: " +
                   "\nping: {}".format(self.ping) +
                   "\nmessage: {}".format(self.message) +
                   "\npinged: {}".format(self.pinged))

        # What was the command?
        if self.pinged:
            pattern = r"^[!,\.\?\"']?([\w^]+)(.*)$"
        else:
            # Force the command to be marked if we weren't pinged
            pattern = r"^[!,\.\?\"']([\w^]+)(.*)$"
        parseprint(self.message)
        match = re.search(pattern, self.message)
        parseprint(match)
        if match:
            # Remove command from the message
            self.command = match.group(1).strip().lower()
            try:
                self.message = match.group(2).strip()
            except IndexError:
                self.message = ""
            parseprint("Doing a " + self.command + "!")
        else:
            # No command - work out what to do here
            parseprint("No command!")
            self.command = False

        # What were the arguments?
        if self.command:
            self.message = shlex.split(self.message)
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
    colours = (180,220,216,209,208,46,
               11,143,113,77,108,71,79,
               37,80,14,39,117,75,69,146,
               205,170,213,177,13,217)
    # Copied from IRCCloud's formatter.js
    nick = nick.lower()
    nick = re.sub(r"[`_]+$", "", nick)
    nick = re.sub(r"\|.*$", "", nick)
    hash = 0
    for i in nick:
        hash = ord(nick[i]) + (hash << 6) + (hash << 16) - hash
    index = hash % length
    return "\x1b[38;5;{}m{}\x1b[0m]".format(colours[index],nick)
    return "probably blue"
