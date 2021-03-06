""" gimmick.py

Container file for gimmick commands.
More commands can be added by request.
"""

from random import choice, randint
from emoji import emojize
import requests

from helpers.defer import defer


class idea:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply(
            "{} · {}".format(
                "http://bit.ly/scp-gen",
                requests.get(
                    "https://scp-generator.herokuapp.com/newscp"
                ).text,
            )
        )


class hug:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if msg.sender == "Jazstar":
            msg.reply("Not in front of the children!")
        elif msg.sender == "ROUNDERHOUSE":
            msg.reply("No thank you.")
        else:
            msg.reply("*hugs*")


class reptile:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = 31 if msg.sender == "CuteGirl" else 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":sauropod:", ":T-Rex:"]))
        msg.reply(output)


class fish:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":fish:", ":tropical_fish:"]))
        msg.reply(output)


class bear:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":bear:"]))
        msg.reply(output)


class cat:
    @classmethod
    def command(cls, irc_c, msg, cmd):
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


class balls:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = randint(2, 15)
        output = ""
        for _ in range(0, repeat):
            output += emojize(
                choice(
                    [
                        ":soccer:",
                        ":volleyball:",
                        ":basketball:",
                        ":football:",
                        ":rugby_football:",
                        ":softball:",
                        ":baseball:",
                        ":8ball:",
                        ":crystal_ball:",
                        ":yarn:",
                    ]
                )
            )
        msg.reply(output)


class narcissism:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if cmd.command == "rounderhouse":
            msg.reply(emojize(":red_circle::house:"))
        if cmd.command == "jazstar":
            msg.reply(emojize(":saxophone::star:"))
        if cmd.command == "themightymcb":
            msg.reply(emojize(":muscle::flag-ie::bee:"))


class password:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("look harder fuckwit")


class fiction:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("https://www.youtube.com/watch?v=ioGoPOAxkCg")


class punctuation:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("dot: · en: – em: — blackbox: █")


class tell:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        if defer.check(cmd, 'jarvis', 'Secretary_Helen'):
            return
        msg.reply("{}: dumbass".format(msg.sender))
