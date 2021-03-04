<script>
  import "@fontsource/libre-franklin/latin-400.css"
  import "@fontsource/libre-franklin/latin-700.css"
  import "./style.css"

  import Commands from "./Commands.svelte"
  import Sections from "./Sections.svelte"
  import Sidebar from "./Sidebar.svelte"
  import Header from "./Header.svelte"
  import Footer from "./Footer.svelte"
</script>

<Sidebar></Sidebar>
<main class="w-full">
  <Header></Header>
  <Sections></Sections>
  <Commands></Commands>
  <Footer></Footer>
</main>
