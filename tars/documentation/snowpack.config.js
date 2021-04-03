const fontLocation = "node_modules/@fontsource/libre-franklin/files/libre-franklin-latin-$weight-normal.$ext"
const putPath = "dist/_snowpack/pkg/@fontsource/libre-franklin"

module.exports = {
  mount: {
    src: "/",
    build: "/",
  },
  plugins: [
    [
      "@snowpack/plugin-run-script",
      {
        name: "Copy Fontsource fonts (snowpackjs/snowpack#1573)",
        cmd: [
          `mkdir -p ${putPath}`,
          ...[
            fontLocation.replace("$weight", "400").replace("$ext", "woff"),
            fontLocation.replace("$weight", "400").replace("$ext", "woff2"),
            fontLocation.replace("$weight", "700").replace("$ext", "woff"),
            fontLocation.replace("$weight", "700").replace("$ext", "woff2")
          ].map(filePath => `cp ${filePath} ${putPath}`)
        ].join(" && ")
      }
    ],
    "@snowpack/plugin-postcss",
    "@snowpack/plugin-svelte",
    "@snowpack/plugin-webpack"
  ],
  buildOptions: {
    out: "dist",
    baseUrl: "./",
  },
  optimize: {
    bundle: true,
    splitting: true,
    treeshake: true,
    manifest: true,
    minify: true,
    target: "es2017"
  }
}
