"""dbq.py

Database Query commands for checking the database.
"""

from pprint import pprint

class query:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if cmd.args['root'][0] == 'tables':
            msg.reply(" ".join(irc_c.db._driver.get_all_tables()))
