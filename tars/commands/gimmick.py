""" gimmick.py

Container file for gimmick commands.
More commands can be added by request.
"""

from random import choice, randint

from emoji import emojize
import requests

from tars.helpers.basecommand import Command


class Idea(Command):
    """Generates a random SCP idea.

    This uses
    [Mikroscopic's idea generator](https://scp-generator.herokuapp.com).
    """

    command_name = "Idea generator"
    aliases = ["idea"]

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
    """Shows your appreciation for TARS physically."""

    command_name = "Hug the bot"
    aliases = ["hug", "hugtars"]

    def execute(self, irc_c, msg, cmd):
        if msg.sender == "Jazstar":
            msg.reply("Not in front of the children!")
        elif msg.sender == "ROUNDERHOUSE":
            msg.reply("No thank you.")
        else:
            msg.reply("*hugs*")


class Reptile(Command):
    aliases = ["reptile", "rep"]

    def execute(self, irc_c, msg, cmd):
        repeat = 31 if msg.sender == "CuteGirl" else 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":sauropod:", ":T-Rex:"]))
        msg.reply(output)


class Fish(Command):
    aliases = ["fish", "reptile+", "rep+"]

    def execute(self, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":fish:", ":tropical_fish:"]))
        msg.reply(output)


class Bear(Command):
    aliases = ["bear"]

    def execute(self, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0, repeat):
            output += emojize(choice([":bear:"]))
        msg.reply(output)


class Cat(Command):
    aliases = ["cat"]

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
    aliases = ["rounderhouse", "jazstar", "themightymcb"]

    def execute(self, irc_c, msg, cmd):
        if cmd.command == "rounderhouse":
            msg.reply(emojize(":red_circle::house:"))
        if cmd.command == "jazstar":
            msg.reply(emojize(":saxophone::star:"))
        if cmd.command == "themightymcb":
            msg.reply(emojize(":muscle::flag-ie::bee:"))


class Password(Command):
    """Helpful hints for newbies for finding the passcode."""

    command_name = "Passcode help"
    aliases = ["passcode"]

    def execute(self, irc_c, msg, cmd):
        msg.reply("look harder fuckwit")


class Fiction(Command):
    """Links to a useful repository for newbies who are wondering if SCP is
    actually real."""

    command_name = "Is this real?"
    aliases = ["isthisreal"]

    def execute(self, irc_c, msg, cmd):
        msg.reply("https://www.youtube.com/watch?v=ioGoPOAxkCg")


class Balls(Command):
    aliases = ["balls"]

    def execute(self, irc_c, msg, cmd):
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


class Punctuation(Command):
    """Quick copy-pastes for common but hard-to-find characters."""

    command_name = "Punctuation"
    aliases = ["punctuation", "punc", "blackbox"]

    def execute(self, irc_c, msg, cmd):
        msg.reply("dot: · en: – em: — blackbox: █")


class Tell(Command):
    """Recommends a method for getting a message to someone.

    TARS intentionally doesn't support `.tell`, so as to avoid causing
    confusion with other bots on the network. It would be a bit of a pain
    sending a message with one bot, only for it to take forever to arrive
    because most of the other user's interactions are with another bot.

    If TARS successfully receives a `.tell` command, which implies that there
    is no other bot present to handle it, it will inform you as such and
    recommend another method. TARS assumes that you meant to use `.tell` in a
    channel with a bot that supports it. The response will hopefully prompt you
    to rewrite your message elsewhere. If TARS didn't respond at all, you might
    not notice and go on with your life, and the message would never be sent.

    You can send a message to any user on SkipIRC using MemoServ with
    @example(/ms send [nick] [message...]), which will even tell you when
    they've read it. This is the method that TARS will recommend.
    """

    command_name = "Tell"
    aliases = ["tell"]

    def execute(self, irc_c, msg, cmd):
        msg.reply(
            "{}: I don't support .tell - try using MemoServ: "
            "/ms send [nick] [message...]".format(msg.sender)
        )
