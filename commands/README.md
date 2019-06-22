# Commands
Each file here represents a command or command group. A command group is a set
of commands that each modify the arguments passed to them and then call a
central command.

`__init__.py` contains the infrastructure that loads commands and the
dictionary containing command aliases.

* **admin.py** - Stuff that directly controls the bot. Not stuff the end user
  should have access to, usually.

* **chevron.py** - For handling chevronning.

* **converse.py** - Messages that aren't commands (along with `.converse`) are
  passed here for simple NLP processing.

* **dbq.py** - For printing stuff from the database directly to the console.
  Should have IRC-based command receipt, but should always fail silently in
  IRC.

* **gimmick.py** - Gimmick commands.

* **info.py** - For outputting static information about the bot.

* **promote.py** - For handling social media promotions. Absolutely staff-only.

* **prop.py** - For manually filling the database.

* **refactor.py** - A container for single-use scripts to refactor the
  database, when necessary.

* **search.py** - The meat of the bot. Searches the database for articles.

* **showmore.py** - Selects data from a list produced by `.search`.
