"""api.py

Get the API keys from the secret files.

wikidot.secret.txt: Contains read-only Wikidot API key.
google.secret.txt: Contains Google CSE API key.
cse.secret.txt: Contains Custom Search Engine ID key.
"""

import os.path

wikidot_api_key = None
google_api_key = None
cse_key = None

try:
    with open(os.path.dirname(__file__) + "/../wikidot.secret.txt") as file:
        wikidot_api_key = file.read()
    with open(os.path.dirname(__file__) + "/../google.secret.txt") as file:
        google_api_key = file.read()
    with open(os.path.dirname(__file__) + "/../cse.secret.txt") as file:
        cse_key = file.read()
except:
    raise
