import gevent
import gevent.event

class Signal:
    def __init__(self):
        self._event = gevent.event.Event()
        self._data = None

    def fire(self, data):
        self._data = data
        self._event.set()
        self.unfire()

    def unfire(self):
        print("Waiting to unfire")
        await_signal()
        print("Unfiring")
        self._event.clear()
        self._data = None

data_signal = Signal()

def emit_signal(data=None):
    data_signal.fire(data)

def await_signal(timeout=None):
    if not data_signal._event.wait(timeout):
        raise TimeoutError
    return data_signal._data

def start_multiple_greenlets():
    gevent.spawn(signal_waiter)
    gevent.spawn(signal_sender)
    gevent.idle()

def signal_sender(data="data string"):
    print("Sending signal with data={}".format(data))
    emit_signal(data=data)

def signal_waiter(timeout=5.0):
    data = await_signal(timeout=timeout)
    print("Signal recieved with data={}".format(data))

for i in range(10):
    start_multiple_greenlets()
