<script>
  import { onMount, tick } from "svelte"

  let sidebarList

  // Wait for everything else to render before constructing the sidebar
  onMount(async () => {
    await tick()
    makeSidebarList()
  })

  function makeSidebarList () {
    const sections = document.getElementsByTagName("section")

    // Construct the sidebar by iterating the document's sections.
    // Each section should have an id, a name, and a data-role indicating its
    // nest depths (section, command or argument).
    Array.from(sections).forEach(section => {
      const id = section.id
      if (!id) {
        return
      }
      const name = section.getAttribute("name")

      // Construct the anchor link
      const link = document.createElement("a")
      link.href = `#${id}`
      link.textContent = name

      // Construct the sidebar list item
      const item = document.createElement("li")
      item.classList.add(section.dataset.role)
      item.appendChild(link)

      // Add the item to the sidebar
      sidebarList.appendChild(item)
    })
  }
</script>

<aside class="sticky h-screen top-0 bottom-0 flex flex-col
              bg-primary-dark md:w-72 lg:w-96">
  <h1 class="text-7xl my-6 text-center font-bold text-primary-light">
    TARS
  </h1>
  <nav id="sidebar" class="w-full overflow-y-scroll text-primary">
    <ul bind:this={sidebarList}
        class="mx-1 p-2">
    </ul>
  </nav>
</aside>

