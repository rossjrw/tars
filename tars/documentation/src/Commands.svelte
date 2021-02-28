<script>
  import docs from "../build/docs.json"
</script>

<h2>command reference</h2>

<section id="commands">
  {#each docs.infos as info}
    <div class="command" id={info.id.toLowerCase()}>
      <h3 class="mt-12">
        {#each info.aliases as alias}<span>{alias}</span>{/each}
      </h3>
      {@html info.help}
      {#if info.arguments.length > 0}
        <ul>
          {#each info.arguments as arg}
            <li>{arg.flags}</li>
          {/each}
        </ul>
      {/if}
    </div>
  {/each}
</section>
