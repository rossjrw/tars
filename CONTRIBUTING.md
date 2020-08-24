Thank you for contributing to TARS development!

## Issues

If you've found a bug or want a feature request, or just want to discuss
something, make an issue.

## Pull requests

Pull requests are the best and maybe only (?) way to contribute code to TARS.

Make a pull request as soon as possible! Feel free to make an empty commit
immediately after forking in order to create one as soon as you know what you
want to change/add:

```shell
git commit -m "Init PR" --allow-empty
```

Github will then allow you to make a draft pull request in which you can
discuss any changes you want to make, solicit feedback, etc. "But but but PR
clutter" fuck no I love PRs

### Strings

Use "double quoted strings" for text that will be displayed to the user or that
depends on database info (for example, error messages). Use 'single quoted
strings' for symbols that are internal-only (for example, dict keys).

### Formatting

At the end of your contribution, make sure to run the *Black* autoformatter:

```shell
pipenv run black .
```

Or, to run Black automatically as a pre-commit hook, install the hook:

```shell
pipenv run pre-commit install
```

You might not like some of the changes it makes to your beautiful code. Neither
do I. Let's both just deal with it.
