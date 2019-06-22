""" gimmick.py

Container file for gimmick commands.
More commands can be added by request.
"""

from random import choice

class hug:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("*hugs*")

class reptile:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = 31 if msg.sender == "CuteGirl" else 2
        output = ""
        for _ in range(0,repeat):
            output += choice(["🦕","🦖"])
        msg.reply(output)

class fish:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        repeat = 2
        output = ""
        for _ in range(0,repeat):
            output += choice(["🐠","🐟"])
        msg.reply(output)

class rounderhouse:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("🔴🏠")

class password:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("look harder fuckwit")
