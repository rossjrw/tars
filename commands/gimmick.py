""" gimmick.py

Container file for gimmick commands.
More commands can be added by request.
"""

from random import choice

from emoji import emojize
import requests

from helpers.command import Command


class Idea(Command):
    """Generates a random SCP idea."""

    command_name = "idea"

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "{} · {}".format(
                "http://scp.bz/idea",
                requests.get(
                    "https://scp-generator.herokuapp.com/newscp"
                ).text,
            )
        )


class Hug(Command):
    """Show your appreciation for TARS physically."""

    def execute(self, irc_c, msg, cmd):
        if msg.sender == "Jazstar":
            msg.reply("Not in front of the children!")
        elif msg.sender == "ROUNDERHOUSE":
            msg.reply("No thank you.")
        else:
            msg.reply("*hugs*")


class Reptile(Command):
    """rawr"""

    def execute(self, irc_c, msg, cmd):
        repeat = 31 if msg.sender == "CuteGirl" else 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":sauropod:", ":T-Rex:"]))
        msg.reply(output)


class Fish(Command):
    """blub blub"""

    def execute(self, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":fish:", ":tropical_fish:"]))
        msg.reply(output)


class Bear(Command):
    """grrr"""

    def execute(self, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":bear:"]))
        msg.reply(output)


class Cat(Command):
    """nyao"""

    def execute(self, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(
                choice(
                    [
                        ":cat:",
                        ":cat2:",
                        ":smirk_cat:",
                        ":joy_cat:",
                        ":scream_cat:",
                        ":pouting_cat:",
                        ":crying_cat_face:",
                        ":heart_eyes_cat:",
                        ":smiley_cat:",
                        ":smile_cat:",
                        ":kissing_cat:",
                    ]
                )
            )
        msg.reply(output)


class Narcissism(Command):
    """Awful requests by awful people"""

    def execute(self, irc_c, msg, cmd):
        if cmd.command == "rounderhouse":
            msg.reply(emojize(":red_circle::house:"))
        if cmd.command == "jazstar":
            msg.reply(emojize(":saxophone::star:"))
        if cmd.command == "themightymcb":
            msg.reply(emojize(":muscle::flag-ie::bee:"))


class Password(Command):
    """Helpful hints for newbies for finding the passcode."""

    def execute(self, irc_c, msg, cmd):
        msg.reply("look harder fuckwit")


class Fiction(Command):
    """Links to a useful repository for newbies who are wondering if SCP is
    actually real."""

    def execute(self, irc_c, msg, cmd):
        msg.reply("https://www.youtube.com/watch?v=ioGoPOAxkCg")
