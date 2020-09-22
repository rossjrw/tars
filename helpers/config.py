""" config.py

Parses the config file. Totally separate to pyaib's implementation, I promise
Exports CONFIG, equal to irc_c.config (probably)
"""

import sys
import yaml

from munch import munchify

from helpers.api import toml_url

argv = sys.argv[1:]
configfile = argv[0] if argv else 'tars.conf'

with open(configfile, 'r') as file:
    print("Getting config object...")
    CONFIG = munchify(yaml.safe_load(file))

# might save me a few keystrokes
CONFIG.nick = CONFIG.IRC.nick
CONFIG.home = CONFIG.channels.home
CONFIG.owner = CONFIG.IRC.owner

# Grab the additional online config
print("Getting additional config from external source...")
CONFIG.external = toml_url(CONFIG.config.location)
print(CONFIG.external.test.message)
