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

## Usage

Extact anywhere then

```
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt --no-cache-dir
python3 bot.py [tars.conf]
```

All modules are from PyPI except:
- pyaib, which is forked here: https://github.com/rossjrw/pyaib
- re2, which is forked here: https://github.com/andreasvc/pyre2

re2 will not be installed from requirements.txt as it has a specific install
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

Command objects (`cmd`) are parsed by argparse. Arguments are accessible from
`cmd.args`, after `cmd.expandargs()` has been called.

`cmd.expandargs()` should be called at the start of command execution, and will
execute argparse. `expandargs` takes a list of lists, which define each
argument of the command. Each list should look like the following:

```python
[type, nargs, "--long", "--altlong", ... , "-s"]
```

*type* should be the type of the argument, either `str`, `int`, `float` or
`bool`. If `bool`, then *nargs* must be `0`.

*nargs* is the number of arguments to be expected, in the same syntax as
argparse.

The remainder of the argument are the possible flag names.

Additionally, a further item can be added to the start of the list: either
`"default"` or `"hidden"`. *default* will prepend that argument to the input
string, making the first argument that option (its *nargs* mut be `'*'`).
*hidden* will hide an option from the help.

A few other important pieces of information:

* `msg` - [pyaib's message object](https://github.com/facebook/pyaib/wiki/Plugin-Writing#message-object)
* `from helpers.database import DB` then `DB.xxx()` - where xxx represents a
  function in helpers/database.py
* `from helpers.config import CONFIG` then `CONFIG.xxx` to access property xxx
  of the configuration file

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
