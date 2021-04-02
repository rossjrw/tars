<script>
  import docs from "../build/docs.json"

  docs.infos.forEach(info => {
    info.subcommands = docs.infos.filter(
      otherInfo => otherInfo.base === info.id
    ).map(otherInfo => otherInfo.id)
  })

  let splitFlag = flag => {
    const [positional, dash, optional] = flag.split(/^(-{1,2})/)
    if (positional === "") {
      return [dash, optional]
    }
    return ["", positional]
  }
</script>

<style>
  /* Emphasise the first line of each command.
   * This is the bit that is the help message on the command line */
  section[data-role=command] > :global(p:first-of-type) {
    @apply font-bold;
    @apply text-primary-lighter;
    @apply text-xl;
  }

  /* Aliases in command titles */
  h3 span:nth-child(3n-2),
  h3 span:nth-child(3n) {
    @apply text-primary-light;
  }
  h3 span:last-child {
    @apply hidden;
  }

  /* Flags in argument titles */
  h4 span:nth-child(3n-2),
  h4 span:nth-child(3n) {
    @apply text-primary;
  }
  h4 span:last-child {
    @apply hidden;
  }

  /* Usage blocks */
</style>

<section id=commands data-role=section name="Command Reference">
  <h2>Command Reference</h2>

  {#each docs.infos as info}
    <section id={info.id.toLowerCase()} name="{info.name}" data-role=command>
      <h3 class="mt-12">
        {#each info.aliases as alias}
          <span>..</span><span>{alias}</span><span>, </span>
        {/each}
      </h3>
      {#if Object.keys(info.defersTo).length > 0}
        <ul>
          {#each Object.entries(info.defersTo) as [alias, conflict]}
            <li>
              The alias <code>{alias}</code> <a href=#deferral>defers</a>
              to {@html
                new Intl.ListFormat("en").format(
                  Object.entries(conflict).map(([botname, prefixes]) => {
                    return `${botname} when used with the prefix${
                      prefixes.length > 1 ? "es" : ""
                    } ${
                      new Intl.ListFormat("en", {type: "disjunction"}).format(
                        prefixes.map(prefix => `<code>${prefix}</code>`)
                      )
                    }`
                  })
                )
              }
            </li>
          {/each}
        </ul>
      {/if}
      {#if info.base === "Command"}
        <div class="usage px-5 py-3">
          <pre class="p-0 inline-block whitespace-normal">
            ..{info.usage}
          </pre>
        </div>
      {/if}
      {@html info.help}
      {#if info.base !== "Command"}
        <p>
          This command extends {info.base} and supports all of its arguments.
        </p>
      {/if}
      {#if info.subcommands.length > 0}
        <p>
          This command is extended by
          {new Intl.ListFormat("en").format(info.subcommands)}, which
          {info.subcommands.length === 1 ? "inherits" : "inherit"} all of its
          arguments.
        </p>
      {/if}
      {#if info.arguments.length > 0}
        {#each info.arguments as arg}
          <section id={arg.id}
                   data-role=argument
                   name={splitFlag(arg.flags[0]).join("")}>
            <h4>
              {#each arg.flags.map(splitFlag) as flag}
                <span>{flag[0]}</span><span>{flag[1]}</span><span>, </span>
              {/each}
            </h4>
            {@html arg.help}
          </section>
        {/each}
      {/if}
    </section>
  {/each}
</section>
