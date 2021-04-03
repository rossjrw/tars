<script>
  import { onMount, tick } from "svelte"

  let sidebar
  let sidebarList

  // Wait for everything else to render before constructing the sidebar
  onMount(async () => {
    await tick()
    const observer = new IntersectionObserver(highlightLinks, {
      root: null,
      threshold: 0,
      rootMargin: "-30px 0px -30px 0px",
    })
    makeSidebarList(observer)
  })

  /**
   * Construct the sidebar by iterating the document's sections.
   * Each section should have an id, a name, and a data-role indicating its
   * nest depths (section, command or argument).
   */
  function makeSidebarList (observer) {
    const sections = document.getElementsByTagName("section")

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

      // Watch the section for intersection with the viewport
      observer.observe(section)
    })
  }

  /**
   * Respond to Intersection Observer events to highlight and unhighlight the
   * appropriate links in the sidebar.
   */
  function highlightLinks (entries) {
    if (sidebarList == null) {
      return
    }
    entries.forEach(entry => {
      const link = sidebarList.querySelector(`[href="#${entry.target.id}"]`)
      if (link == null) {
        return
      }
      if (entry.isIntersecting) {
        link.parentElement.classList.add("selected")
      } else {
        link.parentElement.classList.remove("selected")
      }
    })
    // Scroll the lowest visible element into view
    const lastLink = [...sidebarList.querySelectorAll(".selected")].pop()
    if (lastLink != null) {
      sidebar.scroll({
        top: lastLink.offsetTop - sidebar.offsetHeight / 2,
        behavior: "smooth",
      })
    }
  }

  let sidebarOpen = false

  function toggleSidebar () {
    sidebarOpen = !sidebarOpen
  }
</script>

<div on:click={toggleSidebar}
     class="fixed inset-0 bg-black lg:hidden transition-opacity
            {sidebarOpen ? "opacity-50" : "opacity-0 pointer-events-none"}">
</div>

<aside class="fixed h-screen top-0 bottom-0 left-0 transform
              {sidebarOpen ? "" : "-translate-x-full"} transition-transform
              lg:sticky lg:transform-none
              flex flex-col
              bg-primary-dark lg:w-96">
  <h1 class="text-7xl my-6 text-center font-bold text-primary-light">
    TARS
  </h1>
  <nav bind:this={sidebar}
       class="w-full overflow-y-scroll text-primary relative">
    <ul bind:this={sidebarList}
        class="mx-1 p-2">
    </ul>
  </nav>
</aside>

<button on:click={toggleSidebar}
        class="rounded-full w-20 h-20 bg-primary-dark
               focus:outline-none focus:ring focus:ring-primary
               fixed bottom-8 right-8 lg:hidden">
  <span class="sr-only">Toggle sidebar</span>
  =
</button>
