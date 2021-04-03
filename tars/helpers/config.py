""" config.py

Parses the config file. Totally separate to pyaib's implementation, I promise
Exports CONFIG, equal to irc_c.config (probably)
"""

import yaml

from munch import Munch
import tomlkit

from tars.__main__ import get_args_from_command_line
from tars.helpers.api import toml_url

with open(get_args_from_command_line().config, 'r') as file:
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

# Grab the config for command deferral
print("Getting bot deferral config...")
defer_config = get_args_from_command_line().deferral
if defer_config is None:
    print("No bot deferral config; no commands will defer")
    CONFIG['deferral'] = []
else:
    with open(defer_config, 'r') as file:
        CONFIG['deferral'] = tomlkit.parse(file.read())['bots']
