""" scheduler.py

Exports a schedule object which is used to schedule looping tasks
"""

from functools import partial

from apscheduler.schedulers.gevent import GeventScheduler
from pyaib.plugins import plugin_class

from commands.propagate import propagate
from helpers.config import CONFIG


@plugin_class("scheduler")
class Schedule:
    def __init__(self, irc_c, config):
        self.config = config
        self.scheduler = GeventScheduler()

        self._scheduler_greenlet = self.scheduler.start()

        log_propagation_message = partial(
            irc_c.PRIVMSG,
            CONFIG.external['propagation']['logging']['channel'],
        )

        self.scheduler.add_job(
            propagate.get_all_pages,
            'cron',
            kwargs={'reply': log_propagation_message},
            **self.cron_to_kwargs(
                CONFIG.external['propagation']['all_articles']['often']
            ),
        )
        self.scheduler.add_job(
            propagate.get_recent_pages,
            'cron',
            kwargs={'reply': log_propagation_message},
            **self.cron_to_kwargs(
                CONFIG.external['propagation']['new_articles']['often']
            ),
        )

    @staticmethod
    def cron_to_kwargs(cronstring):
        """Converts a cron string to cron kwargs"""
        crons = cronstring.split(" ")
        if len(crons) != 5:
            raise ValueError("Invalid cron {}".format(cronstring))
        crons = [cron.replace("_", " ") for cron in crons]
        kwargs = {
            'minute': crons[0],
            'hour': crons[1],
            'day': crons[2],
            'month': crons[3],
            'day_of_week': crons[4],
        }
        return kwargs
