<script>
  import "@fontsource/libre-franklin/latin-400.css"
  import "@fontsource/libre-franklin/latin-700.css"
  import "./style.css"

  import Commands from "./Commands.svelte"
  import Sections from "./Sections.svelte"
  import Header from "./Header.svelte"
  import Footer from "./Footer.svelte"
</script>

<aside class="sticky h-screen top-0 bottom-0 flex flex-col
              bg-primary-dark md:w-72 lg:w-96">
  <h1 class="text-7xl my-6 text-center font-bold text-primary-light">
    TARS
  </h1>
  <nav id="sidebar" class="w-full overflow-y-scroll"></nav>
</aside>
<main class="w-full">
  <Header></Header>
  <Sections></Sections>
  <Commands></Commands>
  <Footer></Footer>
</main>
