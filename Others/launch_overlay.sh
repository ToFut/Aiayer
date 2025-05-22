#!/bin/bash
# launch_overlay.sh
# Script to properly launch the overlay UI in its original design

echo "====================================================="
echo "    Launching Original Overlay UI                    "
echo "====================================================="

# Change to project root directory
cd "$(dirname "$0")"

# Check if the backend is running
echo "Checking if backend is running on port 8765..."
if command -v nc &>/dev/null; then
    if ! nc -z localhost 8765 2>/dev/null; then
        echo "⚠️  WARNING: Backend WebSocket server not detected on port 8765"
        echo "The overlay needs a WebSocket server to function properly."
        echo "Make sure to run ./start_backend.sh first."
        read -p "Continue anyway? (y/n): " continue_anyway
        if [[ "$continue_anyway" != "y" ]]; then
            echo "Exiting. Please start the backend first with ./start_backend.sh"
            exit 1
        fi
    else
        echo "✅ Backend WebSocket server is running."
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs/overlay

# Try launching from the overlay directory using proper tauri dev
if [ -d "overlay" ] && [ -d "overlay/src-tauri" ]; then
    cd overlay
    
    # Check if npm and node are available
    if ! command -v npm &> /dev/null; then
        echo "❌ Error: npm is required but not found."
        exit 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.vite/deps/_metadata.json" ]; then
        echo "Installing npm dependencies (this may take a minute)..."
        npm install
        
        if [ $? -ne 0 ]; then
            echo "❌ Error: npm install failed."
            exit 1
        fi
    fi
    
    # Run tauri directly with full output to console
    echo "Starting Tauri overlay in foreground mode (Ctrl+C to stop)..."
    echo "This will show the overlay with its original design, including any custom widgets."
    
    # Use tauri directly instead of through npm
    if [ -f "node_modules/.bin/tauri" ]; then
        echo "Using Tauri CLI from node_modules..."
        node_modules/.bin/tauri dev
    else
        echo "Using npm run tauri..."
        npm run tauri dev
    fi
else
    # Fallback to root directory
    echo "❌ Error: Cannot find overlay/src-tauri directory."
    echo "Looking for alternative paths..."
    
    if [ -d "src-tauri" ]; then
        echo "Found src-tauri in root directory, trying to start from here..."
        
        # Check if npm and node are available
        if ! command -v npm &> /dev/null; then
            echo "❌ Error: npm is required but not found."
            exit 1
        fi
        
        # Install dependencies if needed
        if [ ! -d "node_modules" ] || [ ! -f "node_modules/.vite/deps/_metadata.json" ]; then
            echo "Installing npm dependencies (this may take a minute)..."
            npm install
            
            if [ $? -ne 0 ]; then
                echo "❌ Error: npm install failed."
                exit 1
            fi
        fi
        
        # Run tauri directly
        echo "Starting Tauri overlay in foreground mode (Ctrl+C to stop)..."
        
        # Use tauri directly instead of through npm
        if [ -f "node_modules/.bin/tauri" ]; then
            echo "Using Tauri CLI from node_modules..."
            node_modules/.bin/tauri dev
        else
            echo "Using npm run tauri..."
            npm run tauri dev
        fi
    else
        echo "❌ Error: Cannot find any valid Tauri configuration."
        echo "Please check your project structure and try again."
        exit 1
    fi
fi