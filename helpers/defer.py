"""defer.py

For checking whether a command should defer to jarvis or Secretary_Helen.
"""

class defer:
    @classmethod
    def check(cls, irc_c, msg, *bots):
        """Checks whether or not the bot is in the channel. Takes irc_c, msg
        then bots as strings as separate arguments. Returns boolean."""
        # bots is a tuple of bot names to look for

        # first, get a list of everyone in this channel
        # issue a request for channel member names
        mex = irc_c.RAW("NAMES {}".format(msg.raw_channel))
        # We need to request a list of NAMES from IRC.
        # Problem: we can't just await that data, as it'll be coming from raw
        # So we need to log the NAMES into a database and then wait for
        #   the database to have updated.
        # We'll need to have another function on the go somewhere that's
        #   logging names to the db. We'll also need a db.
        # That function will be in plugins/names.py
        msg.reply("Unable to check NAMES")
