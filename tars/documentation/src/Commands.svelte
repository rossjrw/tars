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
          <ul>
            {#each info.arguments as arg}
              <li>{arg.flags}</li>
            {/each}
          </ul>
        {/if}
      </div>
    </div>
  {/each}
</section>
