"""link.py

Links together command documentation by replacing @-commands.
"""

import itertools
import re

from markdown import markdown

from tars.helpers.config import CONFIG


def process_links(command_infos, other_texts):
    """Iterates through the provided Markdown documents and processes the
    commands that link them together.

    Available commands:

        @repo(name)
        Links to the configured repository with the given link text.

        @example(text)
        Inline example - formats the text as a command example. May not include
        parentheses.

        @example(text)(description)
        Block-level example - formats the text as a command example with an
        explanation. Must be the only thing on the line, but may contain
        parentheses. If the description contains a single hyphen it will be
        considered empty.

        @command(alias)
        Links to the given command. The string provided may be any alias and
        may start with nothing, `.`, or `..`.

        @argument(name)
        Links to the argument with the given name in the current command. Can
        only be used in command or argument documentation, not other text.

        @section(name)
        Links to the section with the given name. Note that the 'name' of a
        section here is the first word in its title.

    All commands may include newlines in their text, which will be ignored in
    the output (by definition as per Markdown).

    Note that while examples will be formatted as code, they will not be
    escaped as such, so any Markdown-active syntax inside them must be escaped.

    `command_infos` must be the information from the registry per extract.py.
    `other_texts` is a list of other Markdown text that will appear in the
    documentation.

    Returns `command_infos` and `other_texts` with the commands replaced with
    either Markdown or HTML as appropriate.
    """

    def replace_link(replace):
        """Executes a replacement function on each of the three replacement
        targets (command docs, argument docs, and other text).
        """
        nonlocal command_infos, other_texts
        for info in command_infos:
            command_id = info['id']
            info['help'] = replace(
                info['help'],
                command_infos=command_infos,
                command_id=command_id,
            )
            for arg in info['arguments']:
                arg['help'] = replace(
                    arg['help'],
                    command_infos=command_infos,
                    command_id=command_id,
                )
        # Cannot link to arguments outside of a command
        if replace is not replace_argument:
            other_texts = [
                replace(text, command_infos=command_infos)
                for text in other_texts
            ]

    replace_link(replace_repo)
    replace_link(replace_block_example)
    replace_link(replace_inline_example)
    replace_link(replace_section)
    replace_link(replace_command)
    replace_link(replace_argument)

    # Add sections, but only in the other_texts bit
    other_texts = [wrap_headers_in_sections(text) for text in other_texts]

    # It's not a link replacement but this is the easiest place to implement
    # this
    replace_link(compile_markdown)

    return command_infos, other_texts


def replace_repo(string, **_):
    """Replaces repo command with repo fragment."""

    def replace(match):
        return "[{}]({})".format(match.group(1), CONFIG['repository'],)

    return re.sub(r"@repo\(([^)]*)\)", replace, string)


def replace_block_example(string, **_):
    """Replaces block-level examples.

    Must be performed before inline examples, because the syntax for
    block-level examples contains the syntax for inline examples.
    """

    def replace(match):
        return "> **Example:** {}{}".format(
            replace_inline_example(match.group(1), allow_paren=True),
            (
                " **&mdash;** {}".format(match.group(2))
                if match.group(2) != "-"
                else ""
            ),
        )

    return re.compile(
        r"""
        (?<=\n)           # Assert starting after a newline
        (@example\(.*?\)) # Capture the code
        \((.+?)\)         # Capture the text
        (?=\n{2,}|\n*\Z)  # Assert position at end of paragraph or string
        """,
        re.VERBOSE | re.DOTALL,
    ).sub(replace, string)


def replace_inline_example(string, *, allow_paren=False, **_):
    """Replaces inline examples."""

    def replace(match):
        return "`{}`".format(format_example(match.group(1)))

    return re.sub(
        r"@example\(([{}]*)\)".format(r"\S\s" if allow_paren else "^)"),
        replace,
        string,
    )


def replace_section(string, **_):
    """Replaces links to sections."""

    def replace(match):
        return "[{}](#{})".format(
            match.group(1).lower().capitalize(), match.group(1).lower()
        )

    return re.sub(r"@section\(([^)]*)\)", replace, string)


def replace_command(string, *, command_infos, **_):
    """Replaces links to commands."""

    def replace(match):
        alias = match.group(1).lstrip(".")
        matching_ids = [
            info['id'] for info in command_infos if alias in info['aliases']
        ]
        assert len(matching_ids) > 0, "no command with alias {}".format(alias)
        return "[..{}](#{})".format(alias, matching_ids[0].lower())

    return re.sub(r"@command\(([^)]*)\)", replace, string)


def replace_argument(string, *, command_infos, command_id, **_):
    """Replaces links to other arguments in the same command."""

    def replace(match):
        argument_name = match.group(1).lstrip("-")
        matching_args = [
            arg
            for info in command_infos
            if info['id'] == command_id
            for arg in info['arguments']
            if arg['flags'][0].lstrip("-") == argument_name
        ]
        if len(matching_args) != 1:
            raise TypeError(
                "{} argument{} named {} in {}".format(
                    "more than one" if len(matching_args) > 0 else "no",
                    "" if len(matching_args) > 0 else "s",
                    argument_name,
                    command_id,
                )
            )
        return "[`--{}`](#{})".format(argument_name, matching_args[0]['id'])

    return re.sub(r"@argument\(([^)]*)\)", replace, string)


def wrap_headers_in_sections(string):
    """Wraps headers and their contents in <section> tags."""

    def replace(match):
        href = match.group(2).lower().split(" ")[0]
        name = match.group(2)
        role = "other"
        # markdown=1 is needed for the "Markdown in HTML" extension which
        # allows markdown to be inside HTML tags
        return "<section {} markdown=1>\n{} {}{}\n</section>\n".format(
            """id={} name="{}" data-role={}""".format(href, name, role),
            match.group(1),
            match.group(2),
            match.group(3),
        )

    pattern = re.compile(
        r"""
        (?:^|\n)         # Assert start of string or just after a newline
        (?<!>\n)         # Assert not followed by a >, which indicates the end
                         #   of a section and therefore that the header that
                         #   follows it has already been wrapped
        (\#{1,6})\s(.*)  # Match a header of a given level and its text
        ([\S\s]*?)       # Match everything that comes after the header
        (?=              # End at one of the following:
          \n\1\s         #   1. A header of the same level
          |\n<\/section> #   2. A closing section tag
          |\n*$          #   3. The end of the string
        )
        """,
        re.VERBOSE,
    )
    while True:
        output = pattern.sub(replace, string)
        if output == string:
            break
        string = output
    return output


def compile_markdown(string, **_):
    """Converts a Markdown string to HTML."""
    # A backtick creates a code block but also escapes the text inside it,
    # which I don't want, so I will do that myself
    code = itertools.cycle(["<code>", "</code>"])
    string = re.sub(r"(?<!\\)`", lambda _: next(code), string)
    html = markdown(string, extensions=['md_in_html'])
    return html


def format_example(example):
    """Adds basic formatting to a command example."""
    span = r"""<span class="{}">\1</span>"""
    replacements = [
        ("(TARS)", "inline-bot-name"),
        (r"(?:(?<=: )|(?<=\.)|(?<=\..))([a-z]+)(?= |$)", "inline-command"),
        (r"(?<= |\[)(--[a-z-]{2,}|-[a-z])(?= |\]|$)", "inline-argument"),
        (r"(\[|\]|\.\.\.|,|{|})", "inline-syntax"),
    ]
    for find, name in replacements:
        example = re.sub(find, span.format(name), example)
    return example
