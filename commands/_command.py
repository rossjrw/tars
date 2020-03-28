"""
_command.py

Provides the base Command class that all commands inherit from.
"""

class Command:
    command_name = None
    arguments = []
    def __new__(cls):
        # TODO expandargs
        pass

    def __init__(self):
        pass
