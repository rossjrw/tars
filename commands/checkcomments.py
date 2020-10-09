"""checkcomments.py

Checks your posts for replies you may have missed.
"""

import json
import re

from bs4 import BeautifulSoup
import feedparser
import inflect

from helpers.config import CONFIG
from helpers.database import DB
from helpers.error import CommandError, MyFaultError, isint

plural = inflect.engine()
plural.classical()
# Templates should be parsed with e.g plural.inflect("".format(**{}))

FORUM_URL = "http://scp-wiki.wikidot.com/forum"

REPORT_BODY = """
{intro}
\\n\\n
{info}
\\n\\n
{forums}
\\n\\n
{footer}
"""

REPORT_INTRO = """
# .checkcomments/.cc report
\\n\\n
`.checkcomments/.cc` is a [{botname}]({repo}) command that
searches forum threads on SCP Wiki EN for replies you might have missed.
\\n\\n
This report will notify you of any replies to posts that you've made, or
replies to threads that you started. You can also
[manually subscribe and unsubscribe]({subscription_thread})
from threads. {botname} doesn't know which threads are the discussion pages of
articles you've posted — hopefully you started that thread by making an author
post. If not, you will need to manually subscribe to it.
"""

REPORT_INFO = """
### Report for {username} :mailbox{mailbox_status}:
\\n\\n
This is a report to check comments for Wikidot user
[{username}](https://www.wikidot.com/user:info/{wd_username}) made since
{time_context} {date}. This report was initiated by IRC user {init_nick}
(`{init_hostmask}`) at {init_date}.
\\n\\n
{sub_parse_error}
\\n\\n
You are subscribed to {sub_thread_count} plural("thread", {sub_thread_count})
and {sub_post_count} plural("post", {sub_post_count}),
including {man_sub_count} plural("manual subscription", {man_sub_count})
and {man_unsub_count} plural("manual unsubscription", {man_unsub_count}).
You have {comment_count} plural("new comment", {comment_count})
in {thread_count} plural("thread", {thread_count})
in {forum_count} plural("forum", {forum_count}).
\\n\\n
{forums}
"""

REPORT_PARSE_ERROR = """
There was an error parsing your subscriptions.
You may wish to fix them and then regenerate this report with `.cc -t {time}`.
"""

REPORT_FORUM = """
##### {forum}
\\n\\n
{comment_count} plural("comment", {comment_count})
in {thread_count} plural("thread", {thread_count}).
\\n\\n
{comments}
"""

REPORT_THREAD = """
1. **:mailbox_with_mail: Thread: [{title}]({url}/t-{wd_thread_id})**
\\n
{replies}
"""

REPORT_THREAD_REPLY = """
  - :envelope: Reply:
[{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id})
by {author} at {date} (page {pageno})
"""

REPORT_THREAD_POST = """
  - :package: Replies to your post:
[{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id}) (page {pageno})
\\n
{replies}
"""

REPORT_THREAD_POST_REPLY = "  {}".format(REPORT_THREAD_REPLY)

REPORT_FOOTER = "# :mailbox_with_no_mail:"


class checkcomments:
    """Checks for new comments."""

    @staticmethod
    def command(irc_c, msg, cmd):
        cmd.expandargs(["author a", "timestamp t"])
        if 'author' in cmd:
            if len(cmd['author']) < 1:
                raise CommandError(
                    "Specify the name of author whose comments you want to "
                    "check. To check your own, just use .cc with no argument."
                )
            author = " ".join(cmd['author'])
        else:
            user_id = DB.get_user_id(msg.sender)
            author = DB.get_wikiname(user_id)
            if author is None:
                raise MyFaultError(
                    "I don't know your Wikidot username. Let me know what it "
                    "is with .alias --wiki [username]"
                )
        if 'timestamp' in cmd:
            if len(cmd['timestamp']) != 1 or not isint(cmd['timestamp'][0]):
                raise CommandError(
                    "--timestamp/-t: Specify a numeric UNIX timestamp."
                )
            timestamp = int(cmd['timestamp'][0])
        else:
            timestamp = 0

        # Job 1: Get subscriptions and unsubscriptions from RSS feed

        sub = {'subs': [], 'unsubs': []}
        sub_parse_error = False

        try:
            sub_feed = feedparser.parse(
                CONFIG.external['cc']['subscriptions']['rss']
            )
            if 'bozo_exception' in sub_feed:
                raise ValueError
            # Cache these subscriptions to file
            with open(CONFIG.cc.feedcache, 'w') as cache:
                json.dump(sub_feed, cache)
        except Exception:
            msg.reply(
                "There was a problem with fetching the subscription thread, "
                "so I have used a cached version."
            )
            with open(CONFIG.cc.feedcache, 'r') as cache:
                sub_feed = json.load(cache)

        sub_posts = [
            entry
            for entry in sub_feed['entries']
            if entry['wikidot_authorname'].lower() == author.lower()
        ]
        if len(sub_posts) > 0:
            # There should be one subscription post per user
            sub_post = sub_posts[0]
            sub_post_body = BeautifulSoup(sub_post['content'][0]['value'])
            url_pattern = re.compile(
                r"""
                ^http://(www\.)?
                (scpwiki\.com|scp-wiki\.wikidot\.com)/
                forum/t-(?P<thread>[0-9]+)
                (/.*)?$
                """,
                re.VERBOSE,
            )
            # If the post fails to parse, flag the error to be reported
            try:
                # Subscriptions are in bullet points
                for command in sub_post_body.select("ul li"):
                    action, href = tuple(command.children)
                    action = action.strip().lower()
                    url_match = url_pattern.search(href)
                    if not url_match:
                        # Probably a URL from an unsupported branch
                        continue
                    wd_thread_id = int(url_match.group('thread'))
                    if action == "subscribe":
                        sub['subs'].append(wd_thread_id)
                    elif action == "unsubscribe":
                        sub['unsubs'].append(wd_thread_id)
                    else:
                        raise ValueError("unknown action {}".format(action))
            except Exception as e:
                sub_parse_error = True

        # Job 2: Compile an object that contains all the relevant posts

        forums = DB.get_forums()

        for forum in forums:
            forum['threads'] = DB.get_forum_threads(forum['id'])
