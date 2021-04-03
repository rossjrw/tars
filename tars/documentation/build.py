"""build.py

Builds the documentation.
"""

import json
from pathlib import Path

from tars.documentation.extract import get_command_info
from tars.documentation.link import process_links


def build():
    """Build the documentation."""
    # Get the information
    infos = get_command_info()
    with Path(__file__).with_name("intro.md").open('r') as intro_file:
        intro = intro_file.read()

    # Process the links and convert to Markdown
    infos, [intro] = process_links(infos, [intro])

    # Output the documentation to a build dir as JSON
    build_dir = Path(__file__).parent / 'build'
    build_dir.mkdir(exist_ok=True)
    with (build_dir / "docs.json").open('w') as output_file:
        output_file.write(json.dumps({'infos': infos, 'other': [intro]}))

    print("Documentation built")
