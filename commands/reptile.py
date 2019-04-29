from random import choice

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

class fuckingnarcissism:
    @classmethod
    def command(cls, irc_c, msg, cmd):
        msg.reply("🔴🏠")
