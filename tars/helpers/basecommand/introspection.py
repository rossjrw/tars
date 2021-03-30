"""introspection.py

Mixin to the base command that allows it to perform self-analysis and make
simple command line documenation.
"""

from tars.helpers.config import CONFIG


class IntrospectionMixin:
    _full_docs = "Full documentation: {}".format(CONFIG['documentation'])
    _specific_docs = "Documentation: {}#{{}}".format(CONFIG['documentation'])

    @classmethod
    def get_intro(cls, *, argument=None, flag=None):
        """Retrieves the intro line for this command or the given argument."""
        intro = lambda string: " ".join(string.split("\n\n")[0].split("\n"))
        if flag is not None:
            argument = cls.get_argument(flag)
        if argument is not None:
            return intro(argument['help'])
        if argument is not None or flag is not None:
            # Shouldn't happen, but just to be sure
            return None
        if cls.__doc__ is None:
            return None
        return intro(cls.__doc__)

    @classmethod
    def get_argument(cls, flag):
        """Gets an argument that matches the given flag. Hyphens optional."""
        flag = flag.strip("-")
        try:
            return next(
                filter(
                    lambda arg: any(f.endswith(flag) for f in arg['flags']),
                    cls.arguments,
                )
            )
        except StopIteration:
            return None

    @classmethod
    def make_command_help_string(cls):
        """Constructs a string for help about this command."""
        if cls.__doc__ is None:
            return "That command exists, but is not documented. {}".format(
                cls._full_docs
            )
        return "Command: \x02..{}\x0F — {} {}".format(
            cls.aliases[0],
            cls.get_intro(),
            cls._specific_docs.format(cls.__name__.lower())
            if cls.command_name is not None
            else "{} ({})".format(
                cls._full_docs, "this command is hidden from documentation",
            ),
        )

    @classmethod
    def make_argument_help_string(cls, argument):
        """Constructs a string for help about a given argument."""
        return "Command: \x02..{}\x0F · {}: \x02{}\x0F — {} {}".format(
            cls.aliases[0],
            "optional argument"
            if argument['flags'][0].startswith("-")
            else "positional argument",
            argument['flags'][0],
            cls.get_intro(argument=argument),
            cls._specific_docs.format(
                "-".join(
                    [cls.__name__.lower(), argument['flags'][0].strip("-"),]
                )
            )
            if argument.get('mode', None) != 'hidden'
            else "{} ({})".format(
                cls._specific_docs.format(cls.__name__.lower()),
                "this argument is hidden from documentation",
            ),
        )
