<script>
  import docs from "../build/docs.json"

  docs.infos.forEach(info => {
    info.subcommands = docs.infos.filter(
      otherInfo => otherInfo.base === info.id
    ).map(otherInfo => otherInfo.id)
  })
</script>

<h2>command reference</h2>

<section id="commands">
  {#each docs.infos as info}
    <div class="command" id={info.id.toLowerCase()}>
      <h3 class="mt-12">
        {#each info.aliases as alias}<span>{alias}</span>{/each}
      </h3>
      <div class="command-info">
        {#if info.base === "Command"}
          <pre>..{info.usage}</pre>
        {/if}
        {@html info.help}
        {#if info.base !== "Command"}
          <p>
            This command extends {info.base} and supports all of its arguments.
          </p>
        {/if}
        {#if info.arguments.length > 0}
          {#each info.arguments as arg}
            <h4 id={arg.id}>
              {#each arg.flags as flag}<span>{flag}</span>{/each}
            </h4>
            {@html arg.help}
          {/each}
        {/if}
      </div>
    </div>
  {/each}
</section>
