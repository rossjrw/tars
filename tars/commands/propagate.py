""" prop.py

For propagating the database with wiki data.
"""

from tars.helpers.api import SCPWiki
from tars.helpers.basecommand import Command
from tars.helpers.error import CommandError
from tars.helpers.parse import nickColor
from tars.helpers.database import DB
from tars.helpers.defer import defer


def prop_print(text):
    """Prints with propagation identifier"""
    print("[{}] {}".format(nickColor("Propagation"), text))


class Propagate(Command):
    """Updates articles' database entries.

    This command is called automatically on a set timer to update articles from
    the Crom API.

    It can also be called manually to force an update or to update specific
    articles.
    """

    command_name = "propagate"
    arguments = [
        dict(
            flags=['--sample'],
            type=bool,
            help="""Propagate a sample set of articles.""",
        ),
        dict(
            flags=['--all'],
            type=bool,
            help="""Propagate all pages on the wiki.""",
        ),
        dict(
            flags=['--seconds'],
            type=int,
            nargs=None,
            help="""Propagate all pages created less than this many seconds
            ago.""",
        ),
        dict(
            flags=['slugs'],
            type=str,
            nargs='*',
            help="""List of page slugs to propagate manually.""",
        ),
    ]

    def execute(self, irc_c, msg, cmd):
        if self['sample']:
            samples = [
                "scp-173",
                "scp-3939",
                "cone",
                "theme:ar",
                "scp-3790",  # should be a collab
            ]
            msg.reply("Adding sample data...")
            Propagate.get_wiki_data_for_pages(samples, reply=msg.reply)
        elif self['all']:
            if not defer.controller(cmd):
                raise CommandError("I'm afriad I can't let you do that.")
            Propagate.get_wiki_data(reply=msg.reply)
        elif 'seconds' in self:
            Propagate.get_wiki_data(reply=msg.reply, seconds=self['seconds'])
        elif len(self['slugs']) > 0:
            Propagate.get_wiki_data_for_pages(self['slugs'], reply=msg.reply)
        else:
            raise CommandError("Bad command")
        msg.reply("Done!")

    @staticmethod
    def get_wiki_data(**kwargs):
        """Gets wiki data for all pages."""
        reply = kwargs.pop('reply', lambda _: None)
        if 'seconds' in kwargs:
            reply(f"Getting wiki data for last {kwargs['seconds']} seconds")
        else:
            reply("Getting wiki data for all pages")
        pages_generator = SCPWiki.get_all_pages(**kwargs)
        for pages in pages_generator:
            for page in pages:
                if page['fullname'].startswith("fragment:"):
                    # Don't want to track fragments
                    continue
                DB.add_article(page, commit=False)
        DB.commit()

    @staticmethod
    def get_wiki_data_for_pages(slugs, **kwargs):
        """Gets wiki data for the pages indicated by the list of slugs."""
        reply = kwargs.pop('reply', lambda _: None)
        reply(f"Gettings wiki data for {len(slugs)} specific pages")
        for slug in slugs:
            page = SCPWiki.get_one_page_meta(slug)
            DB.add_article(page, commit=False)
        DB.commit()
