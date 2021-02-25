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

## Usage

```shell
pipenv run python3 -m tars path/to/config
```

The config files I use are in `config/`.

TARS requires a set of API keys to function correctly. These should be stored
in `config/keys.secret.toml`. More details can be found in `helpers/api.py`.

TARS will use the nick provided in the config file and NickServ password as
defined by the key `irc_password` in `keys.secret.toml`.

## Building documentation

```shell
pipenv run python3 -m tars path/to/config --docs
```

## Testing

```shell
pipenv run pytest
```
Testing is... uh... a little spotty. Tests pass but the suite is not exactly
comprehensive.

## Adding commands

Each major command should be in its own file. Subcommands can be in the same
file as the major command's file.

Create a new file in `commands/` named the same as your major command.

Within this file, create a new class named for the major command that extends
`helpers.basecommand.Command`, with the following properties (all of which are
optional):

* `command_name`: The canonical name of this command, used for documentation;
  if not provided or `None`, this command will not appear in documentation.
* `arguments`: A list of dicts, each of which represents an argument for this
  command. These are passed directly to the argparse [`add_argument`
  constructor](https://docs.python.org/3/library/argparse.html#the-add-argument-method)
  and the keys correspond to its kwargs. However, the following extra keys are
  accepted:
  * `flags`: A list of flags for this argument (will be used as the first
    positional parameter of `add_argument`).
  * `mode`: If `"hidden"`, this argument will not appear in documentation.
  * `permission`: The permission level required to run this command (currently
     boolean, with `true` indicating only a Controller can run it).
  * `type`: The same as `type` from argparse, but can also be the following
    values:
    * `helpers.basecommand.regex_type`: Checks that the arguments correctly
      compile to a regex, and exposes the argument values as compiled regex
      objects.
    * `helpers.basecommand.matches_regex(rgx, reason)`: Checks that the
      provided string matches regex `rgx` (can be a Pattern or a string); if it
      does not, rejects the argument with the given reason. The reason should
      complete the sentence "Argument rejected because the value..."
* `defers_to`: A list of IRC nicks; if any of these nicks are present in the
  channel when the command would be executed, it will not be.
* `permission`: The permission level required to run this command (currently
  boolean, with `true` indicating only a Controller can run it).
* `arguments_prepend`: A string that will be prepended to arguments passed to
  this command. Useful for setting defaults for subcommands.

The class' docstring is used as documentation for the command, although only
the first line will appear on the command line.

The command must have an instance method called `execute`, which is called when
the command is run, that takes the
following arguments (which can be named anything):

* `self`: The command object. Check for argument presence with `'argname' in
  self`. To get the value of the argument, access `self` like a dict:
  `self['argname']`.
* `irc_c`: [pyaib
  context](https://github.com/facebook/pyaib/wiki/Plugin-Writing#context-object)
* `msg`: [pyaib
  message](https://github.com/facebook/pyaib/wiki/Plugin-Writing#message-object)
* `cmd`: A parsed message-like object, similar to `msg` but with more
  properties that are pertinent to this command specifically:
  * `ping`: Whether the bot was pinged by this message.
  * `command`: The command name as typed by the user (may differ from the
    canonical `command_name`).
  * `force`: Whether to bypass the defer step.

To create a subcommand, create a new class that extends the parent command,
with its own docstring and `command_name`. I recommend using
`arguments_prepend` to add command-line flags and then implement the
corresponding functionality in the parent command, but if you must add
an `execute` method to the subcommand, be sure to call the parent's `execute`
method as appropriate.

Edit `commands/__init__.py` and add any commands you created to the `COMMANDS`
dict along with any aliases as a sub-dict. Your command must have at least one
alias, or it won't be able to be called.

Other considerations:

* `nargs` must be either 0 or not present if the `type` is `bool`.
* Most `nargs` values will result in a list being created, except for
  `nargs=None`, which expects a single value and returns it directly.
* The default value for `nargs` of `*` and `+` is an empty list, even if no
  value was actually provided.
* If an argument with `nargs` of `"*"` or `"?"` is not present, `'argname' in
  self` will return `false`; if it _is_ present but no values were provided,
  `'argname' in self` will return `true`, even though either way the value is
  identical (`[]` for `"*"` and `XXX TODO` for `"?"`).
* A boolean arg is always present (and an `'arg' in self` check will always
  return `true`) regardless of whether it was actually specified. If it was not
  specified, its value is `false`.

## Other bits

A few other important pieces of information:

* `msg` - [pyaib's message object](https://github.com/facebook/pyaib/wiki/Plugin-Writing#message-object)
* `from helpers.database import DB` then `DB.xxx()` - where xxx represents a
  function in helpers/database.py
* `from helpers.config import CONFIG` then `CONFIG.xxx` to access property xxx
  of the configuration file
