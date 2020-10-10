"""checkcomments.py

Checks your posts for replies you may have missed.
"""

from functools import reduce
import json
import re

from bs4 import BeautifulSoup
from emoji import emojize
import feedparser
import inflect
import pendulum as pd

from helpers.config import CONFIG
from helpers.database import DB
from helpers.error import CommandError, MyFaultError, isint
from helpers.paste import paste

plural = inflect.engine()
plural.classical(zero=False)
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
""".strip(
    "\n"
)

REPORT_INFO = """
### Report for {username} :mailbox{mailbox_status}:
\\n\\n
This is a report to check comments for Wikidot user
 [{username}](https://www.wikidot.com/user:info/{wd_username}) made since
 {time_context} {date}. This report was initiated by IRC user {init_nick}
 (`{init_hostmask}`) at {init_date}.
\\n\\n
{sub_parse_error}
You are subscribed to {sub_thread_count} plural("thread", {sub_thread_count})
 and {sub_post_count} plural("post", {sub_post_count}),
 including {man_sub_count} plural("manual subscription", {man_sub_count})
 and {man_unsub_count} plural("manual unsubscription", {man_unsub_count}).
 You have {comment_count} plural("new comment", {comment_count})
 in {thread_count} plural("thread", {thread_count})
 in {forum_count} plural("forum", {forum_count}).
""".strip(
    "\n"
)

REPORT_PARSE_ERROR = """
There was an error parsing your subscriptions.
 You may wish to fix them and then regenerate this report with `.cc -t {time}`,
 or contact the bot owner, {owner}, if you believe this is in error.
\\n\\n
""".strip(
    "\n"
)

REPORT_FORUM = """
##### {forum}
\\n\\n
{comment_count} plural("comment", {comment_count})
 in {thread_count} plural("thread", {thread_count}).
\\n\\n
{comments}
""".strip(
    "\n"
)

REPORT_THREAD = """
1. **:mailbox_with_mail: Thread: [{title}]({url}/t-{wd_thread_id})**
\\n
{replies}
""".strip(
    "\n"
)

REPORT_THREAD_REPLY = """
  - :envelope: Reply:
 [{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id})
 by {author} at {date} (page {pageno})
""".strip(
    "\n"
)

REPORT_THREAD_POST = """
  - :package: Replies to your post:
 [{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id}) (page {pageno})
\\n
{replies}
""".strip(
    "\n"
)

REPORT_THREAD_POST_REPLY = """
    - :envelope: Reply:
 [{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id})
 by {author} at {date}
""".strip(
    "\n"
)

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
            manual_time = True
        else:
            timestamp = 0
            manual_time = False

        # Job 1: Get subscriptions and unsubscriptions from RSS feed

        sub = {'subs': [], 'unsubs': []}
        sub_parse_error = False

        try:
            sub_feed = feedparser.parse(CONFIG.external['cc']['subs']['rss'])
            if 'bozo_exception' in sub_feed:
                raise ValueError
            # Cache these subscriptions to file
            with open(CONFIG.cc.feedcache, 'w') as cache:
                json.dump(sub_feed, cache)
        except Exception:
            irc_c.PRIVMSG("#tars", "cc error: could not fetch feed")
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
                    action, link = tuple(command.children)
                    action = action.strip().lower()
                    url_match = url_pattern.search(link.get("href"))
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
                irc_c.PRIVMSG("#tars", "cc error: {}".format(e))
                sub_parse_error = True

        # Job 2: Compile an object that contains all the relevant posts

        def get_replies(post):
            """Takes a post and returns the nested replies."""
            replies = DB.get_post_posts(post['id'])
            for reply in replies:
                reply['replies'] = get_replies(reply)
            return replies

        sub_thread_count = 0
        sub_post_count = 0
        responses = []
        forums = DB.get_forums()
        for forum in forums:
            # 1st layer: forums
            forum['threads'] = []
            threads = DB.get_forum_threads(forum['id'])
            for thread in threads:
                # 2nd layer: threads
                thread['posts'] = []
                # If we're ignoring this thread, skip it entirely
                if thread['wikidot_id'] in sub['unsubs']:
                    continue
                sub_thread_count += 1
                posts = DB.get_thread_posts(thread['id'])
                thread['wikiname'] = (
                    posts[0]['wikiname'] if len(posts) > 0 else None
                )
                for index, post in enumerate(posts):
                    # 3rd layer: posts
                    post['replies'] = get_replies(post)
                    post['pageno'] = index // 12 + 1
                    # The 3rd layer should contain a flattened list of followed
                    # posts and general thread replies
                    # The 4th layer is only for replies to followed posts
                    if post['wikiname'].lower() == author.lower():
                        # This is a followed post. Flatten its replies into a
                        # 4th layer
                        sub_post_count += 1
                        for reply in post['replies']:
                            # 4th layer: post replies
                            post['replies'].extend(reply.pop('replies'))
                        post['replies'].sort(key=lambda r: r['date_posted'])
                        post['replies'] = list(
                            filter(
                                lambda r: r['date_posted'] >= timestamp,
                                post['replies'],
                            )
                        )
                    else:
                        # This is not a followed post. Concat its replies into
                        # the 3rd layer
                        posts.extend(post.pop('replies'))
                        # Those posts are now part of the 3rd layer, so they
                        # will be iterated over in this loop - no need for
                        # recursion
                    # Add this post to the thread based on whether or not we
                    # are subscribed to it
                    if ('replies' in post and len(post['replies']) > 0) or (
                        'replies' not in post
                        and (
                            (thread['wikidot_id'] in sub['subs'])
                            or (thread['wikiname'].lower() == author.lower())
                        )
                    ):
                        thread['posts'].append(post)
                thread['posts'].sort(key=lambda r: r['date_posted'])
                thread['posts'] = list(
                    filter(
                        lambda r: r['date_posted'] >= timestamp,
                        thread['posts'],
                    )
                )
                # Add this thread to the forum if it has any posts
                if len(thread['posts']) > 0:
                    forum['threads'].append(thread)
            forum['threads'].sort(key=lambda t: t['posts'][0]['date_posted'])
            # Add this forum to the responses if it has any threads
            if len(forum['threads']) > 0:
                responses.append(forum)

        # Job 3: Compile the report as a Markdown string

        report = (
            REPORT_BODY.format(
                intro=REPORT_INTRO.format(
                    botname=CONFIG.nick,
                    repo=CONFIG.repository,
                    subscription_thread=CONFIG.external['cc']['subs'][
                        'thread'
                    ],
                ),
                info=plural.inflect(
                    REPORT_INFO.format(
                        username=author,
                        mailbox_status="_closed"
                        if len(responses) == 0
                        else "",
                        wd_username=author.replace(" ", "-"),
                        time_context="the manually entered time of"
                        if manual_time
                        else "the last report, which was at",
                        date=pd.from_timestamp(timestamp).to_datetime_string(),
                        init_nick=msg.sender,
                        init_hostmask=msg.sender.usermask,
                        init_date=pd.now().to_datetime_string(),
                        sub_parse_error=REPORT_PARSE_ERROR.format(
                            time=timestamp, owner=CONFIG.owner
                        )
                        if sub_parse_error
                        else "",
                        sub_thread_count=sub_thread_count + len(sub['subs']),
                        sub_post_count=sub_post_count,
                        man_sub_count=len(sub['subs']),
                        man_unsub_count=len(sub['unsubs']),
                        forum_count=len(responses),
                        thread_count=reduce(
                            lambda count, forum: count + len(forum['threads']),
                            responses,
                            0,
                        ),
                        comment_count=reduce(
                            lambda count, forum: count
                            + reduce(
                                lambda count, thread: count
                                + len(
                                    [
                                        p
                                        for p in thread['posts']
                                        if 'replies' not in p
                                    ]
                                )
                                + reduce(
                                    lambda count, post: count
                                    + (
                                        len(post['replies'])
                                        if 'replies' in post
                                        else 0
                                    ),
                                    thread['posts'],
                                    0,
                                ),
                                forum['threads'],
                                0,
                            ),
                            responses,
                            0,
                        ),
                    )
                ),
                forums="\\n\\n".join(
                    plural.inflect(
                        REPORT_FORUM.format(
                            forum=forum['title'],
                            thread_count=len(forum['threads']),
                            comment_count=reduce(
                                lambda count, thread: count
                                + len(
                                    [
                                        p
                                        for p in thread['posts']
                                        if 'replies' not in p
                                    ]
                                )
                                + reduce(
                                    lambda count, post: count
                                    + (
                                        len(post['replies'])
                                        if 'replies' in post
                                        else 0
                                    ),
                                    thread['posts'],
                                    0,
                                ),
                                forum['threads'],
                                0,
                            ),
                            comments="\\n\\n".join(
                                REPORT_THREAD.format(
                                    title=thread['title'],
                                    url=FORUM_URL,
                                    wd_thread_id=thread['wikidot_id'],
                                    replies="\\n".join(
                                        REPORT_THREAD_REPLY.format(
                                            title=post['title'],
                                            url=FORUM_URL,
                                            wd_thread_id=thread['wikidot_id'],
                                            wd_post_id=post['wikidot_id'],
                                            author=post['wikiname'],
                                            date=pd.from_timestamp(
                                                post['date_posted']
                                            ).to_datetime_string(),
                                            pageno=post['pageno'],
                                        )
                                        if 'replies' not in post
                                        else REPORT_THREAD_POST.format(
                                            title=post['title'],
                                            url=FORUM_URL,
                                            wd_thread_id=thread['wikidot_id'],
                                            wd_post_id=post['wikidot_id'],
                                            pageno=post['pageno'],
                                            replies="\\n".join(
                                                REPORT_THREAD_POST_REPLY.format(
                                                    title=reply['title'],
                                                    url=FORUM_URL,
                                                    wd_thread_id=thread[
                                                        'wikidot_id'
                                                    ],
                                                    wd_post_id=reply[
                                                        'wikidot_id'
                                                    ],
                                                    author=reply['wikiname'],
                                                    date=pd.from_timestamp(
                                                        reply['date_posted']
                                                    ).to_datetime_string(),
                                                )
                                                for reply in post['replies']
                                            ),
                                        )
                                        for post in thread['posts']
                                    ),
                                )
                                for thread in forum['threads']
                            ),
                        )
                    )
                    for forum in responses
                ),
                footer=REPORT_FOOTER,
            )
            .replace("\n", "")
            .replace("\\n", "\n")
        )
        report = emojize(report, use_aliases=True)

        # Job 4: Upload the report

        report_url = paste(report)
        msg.reply(
            "{} comments · full report: {}".format(
                "New" if responses else "No new", report_url
            )
        )
