# Set the current directory as the base for module resolution
$env:NODE_PATH = "$PWD\node_modules"
# Run webpack with the correct path
node .\node_modules\webpack\bin\webpack.js serve --mode development