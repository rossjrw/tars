"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen."""

class defer:
    @classmethod
    def check(cls, irc_c, msg, *bots):
        """Checks whether or not the bot is in the channel. Takes irc_c, msg
        then bots as strings as separate arguments. Returns boolean."""
        # bots is a tuple of bot names to look for

        # first, get a list of everyone in this channel
        # issue a request for channel member names
        mex = irc_c.RAW("NAMES {}".format(msg.raw_channel))
        print(mex)
        for bot in bots:
            pass
