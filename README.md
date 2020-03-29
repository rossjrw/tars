# TARS
IRC bot for IO automation

This README contains instructions for command line usage and implementation
details. End users looking for command instruction should look at the
documentation: https://rossjrw.github.io/tars/help/

## Current state

TARS is not yet finished and has no ETA. TARS is, however, operational.

Documentation is currently far ahead of implementation. Many features described
in the documentation are not yet present.

Development is currently focused on the core implementation, particularly the
internal database.

## Installation

TARS uses [Pipenv](https://github.com/pypa/pipenv) for environment management.

```shell
git clone https://github.com/rossjrw/tars
cd tars
pipenv install --dev
```

## Usage

```shell
pipenv shell
python3 bot.py [tars.conf]
```
or
```shell
pipenv run python3 bot.py [tars.conf]
```

All modules are from PyPI except:
- pyaib, which is forked here: https://github.com/rossjrw/pyaib
- re2, which is forked here: https://github.com/andreasvc/pyre2

re2 will not be installed from Pipfile as it has a specific install
process detailed in its README. TARS will operate fine without re2 but will be
vulnerable to catastrophic backtracking regular expression attacks.

In order to install the `cryptography` dependency of pyaib, you may be
required to run:
`sudo apt-get install build-essential libssl-dev libffi-dev python-dev`

TARS requires at least Python 3.5.2.

TARS requires a set of API keys to function correctly. These should be stored
in `keys.secret.txt`. More details can be found in `helpers/api.py`.

TARS will use the config file given as the command line argument. If none is
provided, it will default to `tars.conf`.

TARS will use the nick provided in the config file and NickServ password as
defined by the key `irc_password` in `keys.secret.txt`.

## Testing

```shell
pipenv run pytest
```
Testing is... uh... a little spotty. Tests pass but the suite is not exactly
comprehensive.

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

A few other important pieces of information:

* `msg` - [pyaib's message object](https://github.com/facebook/pyaib/wiki/Plugin-Writing#message-object)
* `from helpers.database import DB` then `DB.xxx()` - where xxx represents a
  function in helpers/database.py
* `from helpers.config import CONFIG` then `CONFIG.xxx` to access property xxx
  of the configuration file

## Parsing commands

Command objects (`cmd`) are parsed by argparse. Arguments are accessible from
`cmd.args` as a Namespace object or by accessing `cmd` like a dict.

Each command class must have class vars `command_name` as a string, `defers_to`
as a list of strings representing which bots the command defers to, and
`arguments` as a list of dicts.

Each argument dict uses the same keys as argparse - that is, `type`, `nargs`, `help`, optionally `choices` etc. - and a couple more:

* `flags` is a list of the argument's flags. At least one of these should not
  start with `--`, but this is not enforced, and just means that the command
  will not have a root argument.
* `mode` can be `'hidden'`, meaning that the argument will not appear in help
  or in the documentation.

Other considerations:

* `nargs` must be either 0 or not present if the `type` is `bool`.
* `nargs=None` is not allowed. Unless the type is bool, nargs must be set. Use
  1 instead.
* The first line of `help` will appear on command line (IRC) help. The rest
  will appear in documentation.

## Database Structure

<p align="center">
    <img src="https://raw.githubusercontent.com/rossjrw/tars/master/database.png">
</p>

* `user_aliases.type` - 'wiki', 'irc' or 'discord'
* `user_aliases.weight` - 0 by default, 1 if the alias is both an IRC name and
  has been set by `.alias` instead of `/nick`.
* `messages.sender` is the IRC name of the user at the time of the message.
* `articles_authors.metadata` - whether or not this value is derived from the
  page itself or from Attribution Metadata.

`user_aliases` and `articles_authors` are not linked, although aliases of type
'wiki' are be searchable in `articles_authors`.

If `articles.downs` is NULL then this indicates that `articles.ups` is the
net rating, and not the number of upvotes. The ratings have yet to be looked at
in more detail. If `articles.downs` is 0 then the article really does have no
downvotes. This is because the Wikidot API does not provide a method for
distinguishing between upvotes and downvotes.

`articles.rating` is an article's rating. `articles.downs` subtracted from
`articles.ups` is expected to be equal to the rating, but this is not
guaranteed, as ups and downs are the result of a separate, less frequent
query.

`channels.autojoin` ≡ whether or not TARS is currently in a channel.
