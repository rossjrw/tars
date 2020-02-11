from helpers.greetings import bad_command
from helpers.database import DB

class chevron:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        try:
            skip = int(cmd.args['root'][0])
        except ValueError:
            skip = 0
        # subtract 1 because ^ = no skips
        skip = skip - 1
        if skip < 0:
            raise CommandError("Chevron count cannot be less than 0")
        # put a chevron limit here eventually, probably
        try:
            limit = int(cmd.args['root'][1])
        except (IndexError, ValueError):
            limit = 10
        if limit > 50:
            raise CommandError("Chevron limit cannot be greater than 50")
        if limit < 1:
            raise CommandError("Chevron limit cannot be less than 1")
        limit = 50 if limit > 50 else limit
        msg.reply("CHEVRON - skip {} - limit {}".format(skip, limit))
        messages = DB.get_messages_to_command_limit(msg.raw_channel, limit)
        # messages is now a list of messages, with the most recent one last
        # try to get some sort of behaviour from each one
        # 1. Match commands that were ignored because a bot was present
        # 2. Match commands that were not parsed as commands
        # 3. Make links for all SCP numbers
        # 4. Pass message to fullname search (probably remove this one)
