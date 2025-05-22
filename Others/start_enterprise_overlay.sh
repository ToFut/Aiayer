#!/bin/bash

echo "🏢 Starting Enterprise SensAI Overlay System"
echo "=============================================="

# Function to check if backend is running
check_backend() {
    if nc -z 127.0.0.1 8767 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo "🚀 Starting Enterprise Backend Server..."
    cd /Users/segevbin/Desktop/SensAI/Aiayer
    nohup python enterprise_backend_server.py > enterprise_server.log 2>&1 &
    echo $! > backend.pid
    
    # Wait for backend to start
    for i in {1..10}; do
        if check_backend; then
            echo "✅ Backend server started successfully!"
            return 0
        fi
        echo "   Waiting for backend... ($i/10)"
        sleep 1
    done
    
    echo "❌ Failed to start backend server"
    return 1
}

# Function to build and run overlay
start_overlay() {
    echo "🎯 Building and starting Tauri overlay..."
    cd /Users/segevbin/Desktop/SensAI/Aiayer/overlay
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing npm dependencies..."
        npm install
    fi
    
    # Build and run Tauri app
    echo "🔨 Building Tauri overlay..."
    npm run tauri dev
}

# Main execution
echo "🔍 Checking backend server status..."

if check_backend; then
    echo "✅ Backend server is already running on port 8767"
else
    if ! start_backend; then
        echo "❌ Failed to start backend. Exiting."
        exit 1
    fi
fi

echo ""
echo "📋 System Status:"
echo "   Backend: ✅ Running on ws://127.0.0.1:8767"
echo "   Modes: 🤔 Ask | 🤖 Agent | 💡 Suggest | 💬 General"
echo "   Memory: ✅ Semantic Search Enabled"
echo ""

# Start the overlay
start_overlay

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down Enterprise SensAI..."
    
    # Kill backend if we started it
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null
        rm -f backend.pid
        echo "✅ Backend server stopped"
    fi
    
    echo "👋 Enterprise SensAI overlay stopped"
    exit 0
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Keep script running
echo "💡 Press Ctrl+C to stop the enterprise overlay system"
wait