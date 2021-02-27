<script>
  import Page from "./Page.svelte"
  import "@fontsource/libre-franklin/latin-400.css"
  import "@fontsource/libre-franklin/latin-700.css"
  import "./style.css"
</script>

<aside class="sticky h-screen top-0 bottom-0 flex flex-col
              bg-primary-dark md:w-72 lg:w-96">
  <h1 class="text-7xl my-6 text-center font-bold text-primary-light">
    TARS
  </h1>
  <nav id="sidebar" class="w-full overflow-y-scroll"></nav>
</aside>
<main class="w-full">
  <header class="bg-primary text-center text-primary-bright py-6">
    <h1 class="text-9xl font-bold">
      TARS
    </h1>
    <p class="text-xl ml-3">
      command documentation
    </p>
  </header>
  <div class="p-4 max-w-prose mx-auto">
    <Page></Page>
  </div>
  <footer class="bg-primary-darker h-72 flex flex-col text-center
                 justify-center">
    <p>
      <b>TARS</b> by Croquembouche
    </p>
    <figure class="flex justify-center space-x-10 items-center">
      <div class="bg-primary-dim h-6 w-6 rounded-full"></div>
      <a href="https://rossjrw.com/">
        <img src="./logo.min.svg"
             alt="Logo and link to my website"
             class="h-20 my-4 mx-auto">
      </a>
      <div class="bg-primary-dim h-6 w-6 rounded-full"></div>
    </figure>
  </footer>
</main>
