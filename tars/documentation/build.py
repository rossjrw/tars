"""build.py

Builds the documentation.
"""

from pathlib import Path

from tars.documentation.extract import get_command_info
from tars.documentation.link import process_links


def build():
    """Build the documentation."""
    infos = get_command_info()
    print(infos[0]['help'], infos[0]['aliases'])
    with Path(__file__).with_name("intro.md").open('r') as intro_file:
        intro = intro_file.read()
    infos, [intro] = process_links(infos, [intro])
    print(infos[0]['help'])
    print(intro)
