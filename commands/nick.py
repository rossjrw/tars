"""nick.py

For handling aliases and stuff like that.
"""

from helpers.database import DB
from helpers.error import CommandError
from helpers.defer import defer
from helpers.config import CONFIG


class alias:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["add a", "remove r", "list l"])
        if len(cmd.args['root']) > 0:
            nick = cmd.args['root'][0]
        else:
            nick = msg.sender
        # 1. Check if this is the right nick
        # get the user ID
        user_id = DB.get_user_id(nick)
        if user_id is None:
            msg.reply("I don't know anyone called '{}'.".format(nick))
            return
        # 2. Add new aliases
        if 'add' in cmd:
            if nick.lower() != msg.sender.lower() and not defer.controller(
                cmd
            ):
                raise CommandError("You can't add an alias for someone else.")
            aliases = cmd['add']
            # db has add_alias, but that needs user ID
            for alias in aliases:
                if alias.lower() == msg.sender.lower():
                    continue
                if DB.add_alias(user_id, alias, 1):
                    msg.reply(
                        "{} already has the alias {}!".format(nick, alias)
                    )
            msg.reply(
                "Added aliases to {}: {}".format(nick, ", ".join(aliases))
            )
            irc_c.PRIVMSG(CONFIG.home, "{} added alias {}".format(nick, alias))
        if 'remove' in cmd:
            if nick.lower() != msg.sender.lower() and not defer.controller(
                cmd
            ):
                raise CommandError(
                    "You can't remove an alias from someone else."
                )
            aliases = cmd['remove']
            # db has add_alias, but that needs user ID
            for alias in aliases:
                if not DB.remove_alias(user_id, alias, 1):
                    msg.reply(
                        "{} didn't have the alias {}!".format(nick, alias)
                    )
            msg.reply(
                "Removed aliases from {}: {}".format(nick, ", ".join(aliases))
            )
        if 'list' in cmd:
            # get all aliases associated with the user
            aliases = DB.get_aliases(user_id)
            msg.reply(
                "I've seen {} go by the names: {}".format(
                    nick if nick != msg.sender else "you", ", ".join(aliases)
                )
            )
        if not any(['add' in cmd, 'remove' in cmd, 'list' in cmd]):
            raise CommandError(
                "Add or remove aliases to a nick with --add "
                "and --remove. See all nicks with --list"
            )
