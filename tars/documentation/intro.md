TARS is an IRC bot made by [SCP Wiki](http://scp-wiki.wikidot.com/) tech team
member Croquembouche. It operates on SkipIRC, and its database is powered by
SMLT's [Crom](https://crom.avn.sh/). TARS is fully @repo(open source).

TARS is designed with the intention of assisting the Internet Outreach team of
the English-speaking branch of the SCP Wiki by automating social media
promotion; however, I've never actually gotten around to implementing this. For
now it is just a general chat bot, although as far as I'm aware it has the most
powerful search syntax of all SCP bots available.

Come chat with TARS in [`#tars`](http://scp-wiki.wikidot.com/chat-guide) on
SkipIRC.

### Using TARS

Use TARS by issuing commands to it, either in IRC channels that it's in, or in
direct messages to it. The command-line syntax will be familiar to anyone who
has used a Linux command line before, and to anyone who hasn't, it will
hopefully be easy and intuitive.

TARS' command prefix is `..`, so commands look like @example(..gib) and
@example(..search --tag scp). The command prefix `.` also works most of the time
(see @section(Deferral) below).

You can also issue commands by pinging TARS, e.g. @example(TARS: s scp-3211).

### Deferral to other bots

TARS is built to be compatible with the current primary SCP IRC bot, DrMagnus'
[Secretary_Helen](http://helenbot.wikidot.com/), and to provide an unobtrusive
user experience when used in tandem with her.

The goal is that a user on SkipIRC shouldn't have to care which bot
specifically is in the channel they want to run a command in &mdash; common
commands should just work. If there are multiple bots in a channel, only one
of them should respond to a command &mdash; any more than that would annoying.

For a smooth experience for users used to Secretary_Helen, TARS also supports
her command prefix `.` (e.g. @example(.search)). However, for commands that
both bots implement, this only works when she is _not_ present in the channel.
When she _is_ present, TARS assumes that the user intended for that command to
be parsed by her &mdash; TARS will shut up and let her speak. The exception to
this is @command(help).

Each command on this page is marked with whether or not it defers to
Secretary_Helen, but you can also consult [her
documentation](http://helenbot.wikidot.com/usage) to be sure which commands
conflict.

TARS should play nicely with other bots, too. Let me know if you have one on
the network.

To force TARS to parse a command regardless of other bots, either ping it at
the start of the message, or use its command prefix (two dots: `..`).

### Inviting TARS to your channel

You can add TARS to your SkipIRC channel using @command(join). You don't need
to ask my permission for this.

### Deploying TARS yourself

Theoretically another instance of TARS could be deployed on SkipIRC, or an
instance deployed on another IRC network altogether. If you're interested in
doing this, there are instructions for getting set up on the @repo(repository).
I welcome any pull requests that result from your experiments!

### About this documentation

This documentation is built using [Svelte](https://svelte.dev/) and styled with
[Tailwind](https://tailwindcss.com/). The command reference is constructed from
the Python codebase &mdash; every command has an internal
[argparse](https://docs.python.org/library/argparse) object which contains the
documentation. There is no prospective documentation &mdash; the commands are
described as they are, not as they could be; while there are a few undocumented
features, they are all intentional. The documentation is re-built with every
push to the repository, so it is guaranteed to be in sync with the codebase
&mdash; it will never be outdated.
