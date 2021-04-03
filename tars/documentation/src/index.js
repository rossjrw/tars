import App from "./App.svelte"

const app = new App({
  target: document.body,
})

document.body.classList.add(
  "bg-primary-dim", "flex", "relative", "text-green-50"
)

export default app
