"""nick.py

For handling aliases and stuff like that.
"""

from helpers.database import DB
from helpers.error import CommandError, MyFaultError
from helpers.defer import defer
from helpers.config import CONFIG


class alias:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        cmd.expandargs(["add a", "remove r", "wiki wikiname w", "list l"])
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
            if len(aliases) < 1:
                raise CommandError("Provide at least one alias to add.")
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
            if len(aliases) < 1:
                raise CommandError("Provide at least one alias to remove.")
            # db has add_alias, but that needs user ID
            for alias in aliases:
                if not DB.remove_alias(user_id, alias, 1):
                    msg.reply(
                        "{} didn't have the alias {}!".format(nick, alias)
                    )
            msg.reply(
                "Removed aliases from {}: {}".format(nick, ", ".join(aliases))
            )
        if 'wiki' in cmd:
            if nick.lower() != msg.sender.lower() and not defer.controller(
                cmd
            ):
                raise CommandError("You can't change someone else's wikiname.")
            aliases = cmd['wiki']
            if len(aliases) < 1:
                raise CommandError(
                    "Provide the Wikidot username. To see any known aliases, "
                    "including Wikidot username, try .alias --list"
                )
            # Wikidot names can contain spaces, and there can only be one
            # wikiname in the database, so it is safe to concatenate
            wikiname = " ".join(aliases)
            # The wikiname might be taken by another user
            wikiname_owner = DB.get_wikiname_owner(wikiname)
            if wikiname_owner is not None and wikiname_owner != user_id:
                raise MyFaultError(
                    "Another user has claimed that Wikidot username. "
                    "If you think this was in error, contact {} "
                    "immediately.".format(CONFIG['IRC']['owner'])
                )

            current_wikiname = DB.get_wikiname(user_id)
            if current_wikiname == wikiname:
                msg.reply(
                    "{} Wikidot username is already {}!".format(
                        "{}'s".format(nick) if nick != msg.sender else "Your",
                        wikiname,
                    )
                )
            else:
                DB.set_wikiname(user_id, wikiname)
                msg.reply(
                    "Updated {} Wikidot username {}to {}.".format(
                        "{}'s".format(nick) if nick != msg.sender else "your",
                        ""
                        if current_wikiname is None
                        else "from {} ".format(current_wikiname),
                        wikiname,
                    )
                )
        if 'list' in cmd:
            # get all aliases associated with the user
            aliases = DB.get_aliases(user_id)
            wikiname = DB.get_wikiname(user_id)
            msg.reply(
                "I've seen {} go by the names: {}. {}".format(
                    nick if nick != msg.sender else "you",
                    ", ".join(aliases),
                    "I don't know their Wikidot username."
                    if wikiname is None
                    else "Their Wikidot username is {}.".format(wikiname),
                )
            )
        if not any(
            ['add' in cmd, 'remove' in cmd, 'list' in cmd, 'wiki' in cmd]
        ):
            raise CommandError(
                "Usage: "
                "Add/remove aliases to a nick with --add/--remove [nick(s)]. "
                "Update your Wikidot name with --wiki [username]. "
                "See all your known aliases with --list."
            )
