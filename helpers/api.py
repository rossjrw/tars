"""api.py

Gets the API key from the secret file.
"""

import os.path

try:
    with open(os.path.dirname(__file__) + "/../api.secret.txt") as file:
        api_key = file.read()
except:
    raise
