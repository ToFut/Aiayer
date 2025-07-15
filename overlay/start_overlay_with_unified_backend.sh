#!/bin/bash

# Start Overlay with Unified Backend
# This script starts the Svelte overlay that connects to our unified backend

echo "🎉 Starting SensAI Overlay with Unified Backend"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the overlay directory"
    echo "   cd overlay && ./start_overlay_with_unified_backend.sh"
    exit 1
fi

# Check if unified backend is running
echo "🔍 Checking if unified backend is running..."
if curl -s http://localhost:8767 > /dev/null 2>&1; then
    echo "✅ Unified backend is running on port 8767"
else
    echo "⚠️  Warning: Unified backend may not be running"
    echo "   Make sure to start it first:"
    echo "   cd ../sensai_ui2html && python start_unified_system.py"
    echo ""
    echo "   Press Enter to continue anyway, or Ctrl+C to stop..."
    read
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🚀 Starting Svelte development server..."
echo "   The overlay will connect to ws://localhost:8767"
echo "   Open your browser to the URL shown below"
echo ""

# Start the dev server
npm run dev 