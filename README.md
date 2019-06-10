# TARS
IRC bot for IO automation

This README contains instructions for command line usage and implementation
details. End users looking for command instruction should look at the
documentation: https://rossjrw.github.io/tars/help/

Documentation is currently far ahead of implementation. Many features described
in the documentation are not yet present.

All modules are from PyPI except:
- pyaib, which is forked here: https://github.com/rossjrw/pyaib
- re2, which is forked here: https://github.com/andreasvc/pyre2

TARS is written in Python 3.5.2.

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

## Commands

Command objects (`cmd`) consist of a dictionary of lists. Each item in the
dictionary will be named for its flag, and will consist of the list of
arguments that follow the flag.

`cmd.hasarg('argname')` will return whether or not a flag is present in the
command.

`cmd.getarg('argname')` will return the list of arguments that follows that
flag. Where there are no arguments but the flag is present, an empty list will
be returned.

To account for variations in flag names, `cmd.expandargs` can be called on a
list of strings that represent flag transformations. For each entry in the
list, the flag name will be changed to the first entry in the string, delimited
by a space.

`cmd.expandargs(['tags t', 'author a'])` will mean that `.command --tags -a`
means the same as `.command -t --author`. The arguments will be accessible from
`cmd.getarg('tags')` and `cmd.getargs('author')`. `cmd.hasarg('t')` will return
false.

It is up to the command author to ensure that all flags are unique.

The base arguments (those that appear before any flag) are accessible from the
pseudoflag `root`, which will always be present.

`cmd` has a few other properties:
* `cmd.raw` - The original, unparsed message
* `cmd.ping` - The identity of the command's ping, if any
* `cmd.unping` - The original message sans ping
* `cmd.pinged` - Boolean, whether or not the bot was pinged
* `cmd.command` - The identity of the actual command issued
* `cmd.args` - The dictionary of arguments

A few other important pieces of information:

* `msg` - [pyaib's message object](https://github.com/facebook/pyaib/wiki/Plugin-Writing#message-object)
* `irc_c.db._driver.XXX()` - where XXX represents a function in
  helpers/database.py

## Database Structure

![database layout](https://raw.githubusercontent.com/rossjrw/tars/master/database.png)

* `user_aliases.type` - 'wiki', 'irc' or 'discord'
* `user_aliases.weight` - 0 by default, 1 if the alias is both an IRC name and
  has been set by `.alias` instead of `/nick`.
* `messages_xxx.sender` is the IRC name of the user at the time of the message.

`user_aliases` and `articles_authors` are not linked, although aliass of type
'wiki' should be searchable in `articles_authors`.

