import "./logo.min.svg"

import App from "./App.svelte"

const app = new App({
  target: document.body,
})

document.body.classList.add(
  "bg-primary-dim", "flex", "relative", "text-gray-100",
)

export default app
