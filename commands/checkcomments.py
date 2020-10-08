"""checkcomments.py

Checks your posts for replies you may have missed.
"""

from helpers.database import DB
from helpers.error import CommandError, MyFaultError

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
replies to threads that you started. You can also [manually subscribe and
unsubscribe]({subscription_thread}) from threads. {botname} doesn't know which
threads are the discussion pages of articles you've posted — hopefully you
started that thread by making an author post. If not, you will need to manually
subscribe to it.
"""

REPORT_INFO = """
### Report for {username} :mailbox{mailbox_status}:
\\n\\n
This is a report to check comments for Wikidot user
[{username}](https://www.wikidot.com/user:info/{wd_username}) made since
{time_context} {date}. This report was initiated by IRC user {init_nick}
(`{init_hostmask}`) at {init_date}.
\\n\\n
You are subscribed to {sub_thread_count} threads and {sub_post_count} posts, including
{man_sub_count} manual subscriptions and {man_unsub_count} manual
unsubscriptions. You have {comment_count} new comments across {thread_count}
threads in {forum_count} forums.
\\n\\n
{forums}
"""

REPORT_FORUM = """
##### {forum}
\\n\\n
{comment_count} new comments across {thread_count} threads.
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

REPORT_THREAD_POST_REPLY = """
    - :envelope: Reply:
[{title}]({url}/t-{wd_thread_id}/#post-{wd_post_id})
by {author} at {date} (page {pageno})
"""

REPORT_FOOTER = """
# :mailbox_with_no_mail:
"""


class checkcomments:
    """Checks for new comments."""

    @staticmethod
    def command(irc_c, msg, cmd):
        cmd.expandargs(["author a"])
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
