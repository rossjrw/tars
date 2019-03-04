# Parses messages.
# Not a plugin.
import re

class ParsedMessage():
    def __init__(self, message):
        # Make sure the message is a string
        message = str(message)
        # Was TARS pinged?
