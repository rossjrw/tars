import "tailwindcss/tailwind.css"
import "@fontsource/libre-franklin/latin-400.css"
import "@fontsource/libre-franklin/latin-700.css"
import "./logo.min.svg"

import App from "./App.svelte"

const app = new App({
  target: document.body,
})

export default app
