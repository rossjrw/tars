const plugin = require("tailwindcss/plugin")

module.exports = {
  purge: ["./src/**/*.{svelte,js,css}"],
  theme: {
    extend: {
      colors: {
        primary: {
          bright: "#f7f197",
          lighter: "#acdca6",
          light: "#8fbc8f",
          DEFAULT: "#68916F",
          dim: "#40654f",
          dark: "#29453e",
          darker: "#1b2f2b",
        },
      },
      fontFamily: {
        sans: ["\"Libre Franklin\"", "sans-serif"],
      },
    },
  },
  plugins: [
    plugin(({ addUtilities }) => {
      addUtilities({
        ".link-line": {
          display: "inline-block",
          "text-decoration": "underline",
          "text-decoration-style": "dotted",
          "text-decoration-thickness": "1px",
          "text-underline-offset": "0.2rem",
        },
      })
      addUtilities(
        {
          ".link-line-hover": {
            "text-decoration-style": "solid",
            "text-decoration-thickness": "2px",
          },
        },
        { variants: ["hover"] },
      )
    }),
  ],
}
