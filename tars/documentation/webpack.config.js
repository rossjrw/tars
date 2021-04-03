const path = require("path")
const { CleanWebpackPlugin } = require("clean-webpack-plugin")
const HtmlWebpackPlugin = require("html-webpack-plugin")
const TerserPlugin = require("terser-webpack-plugin")

const dev = process.env.NODE_ENV === "development"

module.exports = {
  mode: process.env.NODE_ENV,
  ...(
    dev ? { devtool: "eval-source-map" } : {}
  ),
  entry: {
    main: "./src/index.js",
  },
  output: {
    filename: "bundle.[name].js",
    path: path.resolve(__dirname, "dist"),
    assetModuleFilename: "[name][ext]",
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          "style-loader",
          "css-loader",
          "postcss-loader",
        ],
      },
      { test: /\.(woff2?|svg)$/, type: "asset/resource" },
      {
        test: /.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
            emitCss: true,
            compilerOptions: { dev },
          }
        }
      },
    ],
  },
  optimization: {
    minimize: process.env.NODE_ENV === "production",
    minimizer: [new TerserPlugin({ extractComments: false })],
    usedExports: true,
    splitChunks: {
      chunks: "all",
    },
  },
  plugins: [
    // new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      title: "TARS documentation · rossjrw.com",
      filename: "index.html",
      chunks: ["main"],
      meta: {
        viewport: "width=device-width, initial-scale=1",
        description: "Documentation for TARS, the IRC bot.",
      },
    }),
  ],
}
