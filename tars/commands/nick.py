"""nick.py

For handling aliases and stuff like that.
"""

from tars.helpers.basecommand import Command
from tars.helpers.database import DB
from tars.helpers.error import CommandError, MyFaultError
from tars.helpers.defer import defer
from tars.helpers.config import CONFIG


class Alias(Command):
    """Modify your aliases.

    An alias is an alternate name for yourself. These names are currently only
    used for @command(seen) and to stop the bot from pinging you in search
    results (@command(search) and @command(showmore)) and gibs (@command(gib)).

    This command lets you view, add and remove your aliases.

    Aliases cannot be shared.
    """

    command_name = "alias"
    arguments = [
        dict(
            flags=['nick'],
            type=str,
            nargs=None,
            default="",
            help="""The target whose aliases you want to view or modify.

            If not provided, defaults to yourself i.e. the nick you are
            currently using. You can @argument(list) the aliases of any nick,
            but you can only modify your own aliases.
            """,
        ),
        dict(
            flags=['--add', '-a'],
            type=str,
            nargs='+',
            help="""A list of aliases to add, separated by space.

            If the alias you'd like to add contains a space, wrap it in quotes:
            @example(..alias 007 --add "James Bond").
            """,
        ),
        dict(
            flags=['--remove', '-r'],
            type=str,
            nargs='+',
            help="""A list of aliases to remove, separated by space.""",
        ),
        dict(
            flags=['--list', '-l'],
            type=bool,
            help="""Lists the aliases associated with this nick.""",
        ),
        dict(
            flags=['--wikiname', '-w'],
            type=str,
            nargs=None,
            help="""Sets the Wikidot username associated with this IRC
            nick.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        if self['nick'] == "":
            self['nick'] = msg.sender
        # 1. Check if this is the right nick
        # get the user ID
        user_id = DB.get_user_id(self['nick'])
        if user_id is None:
            msg.reply("I don't know anyone called '{}'.".format(self['nick']))
            return
        # 2. Add new aliases
        if len(self['add']) > 0:
            if self[
                'nick'
            ].lower() != msg.sender.lower() and not defer.controller(cmd):
                raise CommandError("You can't add an alias for someone else.")
            for alias in self['add']:
                if DB.add_alias(user_id, alias, 1):
                    msg.reply(
                        "{} already has the alias {}!".format(
                            self['nick'], alias
                        )
                    )
            msg.reply(
                "Added aliases to {}: {}".format(
                    self['nick'], ", ".join(self['alias'])
                )
            )
            irc_c.PRIVMSG(
                CONFIG['channels']['home'],
                "{} added alias {}".format(self['nick'], self['alias']),
            )
        if len(self['remove']) > 0:
            if self[
                'nick'
            ].lower() != msg.sender.lower() and not defer.controller(cmd):
                raise CommandError(
                    "You can't remove an alias from someone else."
                )
            for alias in self['remove']:
                if not DB.remove_alias(user_id, alias, 1):
                    msg.reply(
                        "{} didn't have the alias {}!".format(
                            self['nick'], alias
                        )
                    )
            msg.reply(
                "Removed aliases from {}: {}".format(
                    self['nick'], ", ".join(self['remove'])
                )
            )
        if 'wikiname' in self:
            if self[
                'nick'
            ].lower() != msg.sender.lower() and not defer.controller(cmd):
                raise CommandError("You can't change someone else's wikiname.")
            # The wikiname might be taken by another user
            wikiname_owner = DB.get_wikiname_owner(self['wikiname'])
            if wikiname_owner is not None and wikiname_owner != user_id:
                raise MyFaultError(
                    "Another user has claimed that Wikidot username. "
                    "If you think this was in error, contact {} "
                    "immediately.".format(CONFIG['IRC']['owner'])
                )

            current_wikiname = DB.get_wikiname(user_id)
            if current_wikiname == self['wikiname']:
                msg.reply(
                    "{} Wikidot username is already {}!".format(
                        "{}'s".format(self['nick'])
                        if self['nick'].lower() != msg.sender.lower()
                        else "Your",
                        self['wikiname'],
                    )
                )
            else:
                DB.set_wikiname(user_id, self['wikiname'])
                msg.reply(
                    "Updated {} Wikidot username {}to {}.".format(
                        "{}'s".format(self['nick'])
                        if self['nick'].lower() != msg.sender.lower()
                        else "your",
                        ""
                        if current_wikiname is None
                        else "from {} ".format(current_wikiname),
                        self['wikiname'],
                    )
                )
                irc_c.PRIVMSG(
                    CONFIG['channels']['home'],
                    "{} set wikiname {}".format(
                        self['nick'], self['wikiname']
                    ),
                )
        if self['list']:
            # get all aliases associated with the user
            aliases = DB.get_aliases(user_id)
            wikiname = DB.get_wikiname(user_id)
            msg.reply(
                "I've seen {} go by the names: {}. {}".format(
                    self['nick'] if self['nick'] != msg.sender else "you",
                    ", ".join(aliases),
                    "I don't know {} Wikidot username.".format(
                        "their" if self['nick'] != msg.sender else "your",
                    )
                    if wikiname is None
                    else "{} Wikidot username is {}.".format(
                        "Their" if self['nick'] != msg.sender else "Your",
                        wikiname,
                    ),
                )
            )
