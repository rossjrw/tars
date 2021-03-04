<script>
  import { onMount, tick } from "svelte"

  let sidebarList

  // Wait for everything else to render before constructing the sidebar
  onMount(async () => {
    await tick()
    makeSidebarList()
  })

  function makeSidebarList () {
    const headers = document.querySelectorAll("h2, h3, h4")
    Array.from(headers).forEach(header => {
      const id = header.id
      if (!id) {
        return
      }
      const name = (
        header.hasAttribute("name") ?
        header.getAttribute("name") :
        header.textContent
      )

      // Construct the anchor link
      const link = document.createElement("a")
      link.href = `#${id}`
      link.textContent = name

      // Construct the sidebar list item
      const item = document.createElement("li")
      item.classList.add(header.tagName.toLowerCase())
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

