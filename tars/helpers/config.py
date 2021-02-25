""" config.py

Parses the config file. Totally separate to pyaib's implementation, I promise
Exports CONFIG, equal to irc_c.config (probably)
"""

import yaml

from munch import Munch

from tars.__main__ import get_config_from_command_line
from tars.helpers.api import toml_url

with open(get_config_from_command_line(), 'r') as file:
    print("Getting config object...")
    CONFIG = Munch.fromDict(yaml.safe_load(file))

# might save me a few keystrokes
CONFIG['nick'] = CONFIG['IRC']['nick']
CONFIG['home'] = CONFIG['channels']['home']
CONFIG['owner'] = CONFIG['IRC']['owner']

# Grab the additional online config
print("Getting additional config from external source...")
external_config = toml_url(CONFIG.config.location)
CONFIG.external = external_config
print(CONFIG.external['test']['message'])
