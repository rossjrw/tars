""" scheduler.py

Exports a schedule object which is used to schedule looping tasks
"""

from apscheduler.schedulers.gevent import GeventScheduler
from pyaib.plugins import plugin_class

from helpers.config import CONFIG


def send_a_message_to_home(irc_c):
    irc_c.PRIVMSG(CONFIG.home, "hello!")


@plugin_class("scheduler")
class Schedule:
    def __init__(self, irc_c, config):
        self.config = config
        self.scheduler = GeventScheduler()

        self._scheduler_greenlet = self.scheduler.start()

        self.scheduler.add_job(
            send_a_message_to_home, 'cron', args=[irc_c], second="0,30"
        )
