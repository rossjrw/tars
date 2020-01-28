import random
import gevent
import gevent.event

import gevent.queue

class Signal(object):
    def __init__(self):
        self.__event = gevent.event.Event()
        self.__waiters = []

    def fire(self, data):
        "Only waiters waiting when the fire() came in see the *data*"
        waiters = list(self.__waiters)
        self.__waiters.clear()
        gevent.spawn(self._notify, waiters, data)

    @staticmethod
    def _notify(waiters, data):
        for q in waiters:
            q.put_nowait(data)

    def wait(self, timeout):
        q = gevent.queue.Channel()
        self.__waiters.append(q)
        return q.get(timeout)

data_signal = Signal()

def emit_signal(data=None):
    data_signal.fire(data)

def await_signal(timeout=None):
    return data_signal.wait(timeout)

def start_multiple_greenlets():
    gevent.spawn(signal_waiter)
    gevent.spawn(signal_sender)
    gevent.idle()

def signal_sender():
    data = random.randrange(20)
    print("Sending signal with data={}".format(data))
    emit_signal(data=data)

def signal_waiter(timeout=5.0):
    data = await_signal(timeout=timeout)
    print("Signal recieved with data={}".format(data))

for i in range(10):
    start_multiple_greenlets()
