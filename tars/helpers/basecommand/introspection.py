"""introspection.py

Mixin to the base command that allows it to perform self-analysis.
"""


class IntrospectionMixin:
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
