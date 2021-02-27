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
    filename: "bundle.[contenthash].js",
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
          {
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                plugins: ["tailwindcss", "autoprefixer"],
              },
            },
          },
        ],
      },
      { test: /\.(woff2?|svg)$/, type: "asset/resource" },
      {
        test: /.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
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
  },
  plugins: [
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      title: "TARS Documentation · rossjrw.com",
      filename: "index.html",
      chunks: ["main"],
      meta: { viewport: "width=device-width, initial-scale=1" },
    }),
  ],
}
