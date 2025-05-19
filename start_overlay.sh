#!/bin/bash
# start_overlay.sh
# Script to start the ChatGPT-like overlay UI

echo "====================================================="
echo "    Starting Aiayer Overlay UI                       "
echo "====================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is required but not installed."
    echo "Please install Node.js and npm first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not installed."
    echo "Please install npm first."
    exit 1
fi

# Check if backend is running by checking if the WebSocket server is accessible
echo "Checking if backend is running on port 8765..."
if command -v nc &>/dev/null; then
    if ! nc -z localhost 8765 2>/dev/null; then
        echo "⚠️ Warning: WebSocket server on port 8765 is not accessible."
        echo "Make sure to run start_backend.sh first."
        read -p "Do you want to continue anyway? (y/n): " continue_anyway
        if [[ "$continue_anyway" != "y" ]]; then
            echo "Exiting. Please start the backend first with ./start_backend.sh"
            exit 1
        fi
    else
        echo "✅ Backend WebSocket server is running."
    fi
else
    echo "⚠️ Warning: Unable to check if backend is running (nc command not available)."
    echo "Make sure you've started the backend with ./start_backend.sh"
fi

# Change to project root directory
cd "$(dirname "$0")"

# Navigate to the overlay directory
if [ -d "overlay" ] && [ -d "overlay/src" ]; then
    # If overlay exists and has src subdirectory, use it
    cd overlay
    echo "Using overlay directory"
elif [ -d "src-tauri" ]; then
    # We're already in the right directory
    echo "Using Tauri from current directory"
elif [ -d "src" ] && [ -d "src-tauri" ]; then
    # We're in the right directory, no need to change
    echo "Already in the root directory with src and src-tauri"
else
    echo "❌ Error: Could not find proper Tauri project structure."
    echo "Expected either:"
    echo "  - overlay/src and overlay/src-tauri directories"
    echo "  - src and src-tauri directories in current folder"
    
    # Debug output to help diagnose the issue
    echo ""
    echo "Current directory structure:"
    ls -la
    
    # Exit with error
    exit 1
fi

# Install dependencies if node_modules doesn't exist or is empty
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
    echo "Installing npm dependencies (this may take a minute)..."
    npm install
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: npm install failed."
        echo "Try running 'npm install' manually to see the full error."
        exit 1
    fi
    
    echo "✅ Dependencies installed successfully."
else
    echo "✅ Dependencies already installed."
fi

# Check if Vite CLI is accessible
if [ ! -f "node_modules/vite/dist/node/cli.js" ]; then
    echo "⚠️ Warning: Vite CLI not found in expected location."
    echo "Reinstalling Vite..."
    npm install vite
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Vite installation failed."
        exit 1
    fi
fi

# Start Tauri
echo "Starting Tauri overlay..."
npm run tauri dev

# If npm run tauri dev exits, show this message
echo "
Overlay UI has exited. If you encountered any issues:

1. Make sure backend is running with ./start_backend.sh
2. Check for errors in the npm output above
3. Try running 'npm run tauri dev' manually
4. If dependencies issues persist, try 'rm -rf node_modules && npm install'
"