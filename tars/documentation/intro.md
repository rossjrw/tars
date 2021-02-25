### What is TARS?

TARS is an IRC bot made by SCP Wiki tech team member Croquembouche. It operates
on SkipIRC, and its database is powered by SMLT's Crom API. TARS is fully
@repo(open source).

TARS is designed with the intention of assisting the Internet Outreach team of
the English-speaking branch of the SCP Wiki by automating social media
promotion; however, I've never actually gotten around to implementing this. For
now it is just a general chat bot, although it boasts (I believe) the most
powerful search syntax of all SCP bots available.

### Using TARS

Use TARS by issuing commands to it, either in IRC channels that it's in, or in
direct messages to it. The command-line syntax will be familiar to anyone who
has used a Linux command line before, and to anyone who hasn't, it will
hopefully be easy and intuitive.

TARS' command prefix is `..`, so commands look like @example(..gib) and
@example(..search --tag scp). The command prefix `.` also works most of the time
(see @section(Deferral) below).

You can also issue commands by pinging TARS, e.g. @example(TARS: s scp-3211).

### Deferral (to other bots)

If someone posts a command like @command(.help) in a channel, if there are
multiple bots there, they may all try to respond at once!

TARS is built to be compatible with the current primary SCP IRC bot: DrMagnus'
Secretary_Helen, and to provide an unobtrusive user experience when used in
tandem with her. As a result, TARS also supports the command prefix `.` (e.g.
@example(.search)). However, for commands that Secretary_Helen implements, this
only works when Secretary_Helen is _not_ present in the room. When she is
present, that command is expected to be parsed by her, and TARS will shut up
and let her speak.

To force TARS to parse a command, either ping it at the start of the message,
or prefix the command with two dots (`..`).

### Adding TARS to your channel

You can add TARS to your SkipIRC channel using @command(join). You don't need
to ask my permission for this.

### Deploying TARS yourself

Theoretically another instance of TARS could be deployed on SkipIRC, or an
instance deployed on another IRC network altogether. There are instructions for
getting set up on the @repo(repository).
