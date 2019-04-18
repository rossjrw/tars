"""converse.py

Responses for regular messages - ie, not commands.
"""

class converse:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        # Recieves text in msg.message
        msg.reply(str(cmd))

    @staticmethod
    def strip(string):
        return ''.join(l for l in string if l.isalnum()).lower()
