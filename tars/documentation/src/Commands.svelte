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

<h2 id="commands">Command Reference</h2>

<section>
  {#each docs.infos as info}
    <div class="command">
      <h3 class="mt-12" name={info.name} id={info.id.toLowerCase()}>
        {#each info.aliases as alias}
          <span>..</span><span>{alias}</span><span>, </span>
        {/each}
      </h3>
      {#if info.base === "Command"}
        <div>
          <pre>..{info.usage}</pre>
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
          <h4 id={arg.id}>
            {#each arg.flags.map(splitFlag) as flag}
              <span>{flag[0]}</span><span>{flag[1]}</span><span>, </span>
            {/each}
          </h4>
          {@html arg.help}
        {/each}
      {/if}
    </div>
  {/each}
</section>
