#!/bin/bash
# GharMitra Standalone Backend Server
# This script starts the backend in standalone mode for demo

echo "========================================"
echo "GharMitra Standalone Backend Server"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "Installing dependencies..."
python3 -m pip install --upgrade pip --quiet
pip install -r requirements.txt

# Setup .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Setting up .env file..."
    python3 setup_standalone_env.py
    if [ $? -ne 0 ]; then
        echo ""
        echo "Creating basic .env file..."
        cat > .env << EOF
DEPLOYMENT_MODE=standalone
DATABASE_URL=sqlite+aiosqlite:///./GharMitra.db
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION
ENCRYPTION_KEY=CHANGE_THIS_IN_PRODUCTION
EOF
        echo ""
        echo "WARNING: Please update .env with secure SECRET_KEY and ENCRYPTION_KEY!"
        echo "Run: python3 setup_standalone_env.py"
        echo ""
        read -p "Press Enter to continue..."
    fi
fi

# Get local IP address
echo ""
echo "Getting local IP address..."
python3 get_local_ip.py
echo ""

# Start the server
echo "========================================"
echo "Starting GharMitra Backend Server..."
echo "========================================"
echo ""
echo "Server will be available at:"
echo "  - Local: http://localhost:${PORT:-8001}"
echo "  - Network: http://[YOUR_IP]:${PORT:-8001}"
echo ""
echo "API Documentation: http://localhost:${PORT:-8001}/docs"
echo "Health Check: http://localhost:${PORT:-8001}/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Set default port (8001 to avoid conflict with other projects)
PORT=${PORT:-8001}

echo ""
echo "NOTE: Using port $PORT (to avoid conflict with other projects)"
echo "      To change port, set PORT environment variable or edit .env file"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload


