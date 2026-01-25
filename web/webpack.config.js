const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    clean: true,
    publicPath: '/',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              ['@babel/preset-react', { runtime: 'automatic' }],
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
        exclude: /node_modules/,
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/i,
        type: 'asset/resource',
      },
      {
        test: /\.(mp4|webm|ogg)$/i,
        type: 'asset/resource',
      },
    ],
  },
  resolve: {
    alias: {
      'react-native$': 'react-native-web',
      '@react-native-async-storage/async-storage$': path.resolve(__dirname, 'src/utils/storage.js'),
    },
    extensions: ['.web.js', '.web.jsx', '.js', '.jsx', '.json', '.ts', '.tsx'],
    fallback: {
      "crypto": false,
      "stream": false,
      "buffer": false,
    },
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
      filename: 'index.html',
      inject: true,
    }),
    new webpack.DefinePlugin({
      'process.env.REACT_APP_API_URL': JSON.stringify(process.env.REACT_APP_API_URL || 'http://localhost:8001/api'),
    }),
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'public',
          to: '',
          globOptions: {
            ignore: ['**/index.html'], // index.html is handled by HtmlWebpackPlugin
          },
        },
      ],
    }),
  ],
  devServer: {
    port: 3006,
    host: 'localhost',
    hot: true,
    open: ['/'],
    historyApiFallback: {
      index: '/index.html',
      disableDotRule: true,
    },
    static: [
      {
        directory: path.join(__dirname, 'public'),
        publicPath: '/',
        watch: false, // Don't watch public folder, only use it as template
      },
    ],
    compress: true,
    liveReload: true,
    devMiddleware: {
      publicPath: '/',
      writeToDisk: false, // Serve from memory in dev mode
    },
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
      progress: true,
      logging: 'info',
    },
    onListening: function (devServer) {
      if (!devServer) {
        throw new Error('webpack-dev-server is not defined');
      }
      const port = devServer.server.address().port;
      console.log(`\n✅ GharMitra dev server running on http://localhost:${port}\n`);
    },
  },
  devtool: 'source-map',
};

