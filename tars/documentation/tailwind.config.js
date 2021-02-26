const plugin = require("tailwindcss/plugin");

module.exports = {
  purge: [ './src/**/*.html' ],
  // theme: {
  //   extend: {
  //     fontFamily: {
  //       display: ['Aileron', 'sans-serif'],
  //       sans: ['"Libre Franklin"', 'sans-serif'],
  //       serif: ['Lora', 'serif']
  //     },
  //   },
  // },
  plugins: [
    plugin(({ addUtilities }) => {
      addUtilities({
        '.link-line': {
          'display': 'inline-block',
          'text-decoration': 'underline',
          'text-decoration-style': 'dotted',
          'text-decoration-thickness': '1px'
        }
      })
      addUtilities(
        {
          '.link-line-hover': {
            'text-decoration-style': 'solid',
            'text-decoration-thickness': '2px',
          }
        },
        { variants: ['hover'] }
      )
    })
  ]
}
