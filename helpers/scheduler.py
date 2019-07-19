""" scheduler.py

Theoretically, this will be used to schedule looping tasks
"""

import time
from datetime import timedelta

start_time = time.time()

def uptime():
    return str(timedelta(seconds=round(time.time()-start_time)))

def get_attribution_metadata():
    pass
