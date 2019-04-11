# TARS
IRC bot for IO automation

Check here for documentation: https://rossjrw.github.io/tars/help/

## Usage

Extact anywhere then

```
python3 bot.py [-p password] [-n name]
```

where password is TARS' NickServ password and name is the bot's name.

## Adding commands

Each major command should be in its own file. Subcommands can be in the same file
as the major command's file.

Create a new file in `commands/` named the same as your major command.

Within this file, create a new `class` with the (lowercase) name of the major
command. Add an `aliases` property with a list of any aliases for the command.

Within the class, create a new class method called `command` that takes
arguments `irc_c`, `msg` and `cmd`, where irc_c is pyaib's irc context and msg
is pyaib's message object, and cmd is the message as a parsed command.

Edit `commands/__init__.py` and add any commands you created to the `COMMANDS`
dict along with any aliases as a sub-dict. Your command must have at least one
alias, or it won't be able to be called.

## Database Structure

![database layout](https://raw.githubusercontent.com/rossjrw/tars/master/database.png)
