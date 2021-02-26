const path = require("path")
const {CleanWebpackPlugin} = require("clean-webpack-plugin")
const HtmlWebpackPlugin = require("html-webpack-plugin")
const TerserPlugin = require("terser-webpack-plugin")

module.exports = {
  mode: process.env.NODE_ENV,
  ...(
    process.env.NODE_ENV === "development"
    ? { devtool: "eval-source-map" }
    : {}
  ),
  entry: {
    main: "./src/index.js",
  },
  output: {
    filename: "bundle.[contenthash].js",
    path: path.resolve(__dirname, "dist"),
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader',
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [ 'tailwindcss', 'autoprefixer' ]
              }
            }
          }
        ]
      },
    ],
  },
  optimization: {
    minimize: process.env.NODE_ENV === "production",
    minimizer: [ new TerserPlugin({ extractComments: false }) ],
    usedExports: true
  },
  plugins: [
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      template: "./src/index.jinja.html",
      filename: "index.html",
      chunks: ["main"],
    }),
  ],
};
