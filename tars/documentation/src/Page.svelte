<script>
  import docs from "../build/docs.json"
</script>

<h2 id="intro" class="hidden">Introduction</h2>

{@html docs.other}

<h2 id="commands">Commands</h2>

{#each docs.infos as info}
  <section class="my-12">
    <h3 id={info.id.toLowerCase()}
        class="font-bold text-5xl mb-4">
      ..{info.aliases.join(", ..")}
    </h3>
    {@html info.help}
    {#each info.arguments as arg}

    {/each}
  </section>
{/each}
