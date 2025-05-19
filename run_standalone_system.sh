#!/bin/bash

echo "====================================================="
echo "    Starting Standalone Aiayer System                "
echo "====================================================="

# 1. Stop any existing processes
echo "Stopping any running services..."
pkill -f "python.*ws" 2>/dev/null || true
sleep 1

# 2. Start the ultra-minimal standalone WebSocket server
echo "Starting the ultra-minimal standalone WebSocket server..."
python3 ./ultra_minimal_ws_server.py &
WS_PID=$!
sleep 2

# 3. Check if server is running
if ps -p $WS_PID > /dev/null; then
    echo "✅ Standalone WebSocket server started on port 8765"
else
    echo "❌ Standalone WebSocket server failed to start"
    exit 1
fi

# 4. Start Tauri overlay in a separate terminal
echo "Starting Tauri overlay in a new terminal window..."
cat > /tmp/start_tauri_standalone.sh << 'EOF'
#!/bin/bash
echo "Starting Tauri overlay..."
cd "$(dirname "$0")"
cd ./overlay

# Make sure dependencies are installed
echo "Checking npm dependencies..."
if [ ! -d "node_modules" ] || [ ! -d "node_modules/vite" ]; then
    echo "Installing npm dependencies (this may take a minute)..."
    npm install
fi

# Run Tauri
echo "Starting Tauri..."
npm run tauri dev
EOF

chmod +x /tmp/start_tauri_standalone.sh

# Start a new terminal to run Tauri
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '$PWD' && /tmp/start_tauri_standalone.sh"'
else
    # Linux and others
    echo "Please open a new terminal window and run:"
    echo "cd $PWD/overlay && npm install && npm run tauri dev"
fi

echo "
=====================================================
    Standalone Aiayer System Running
=====================================================

COMPONENTS:
1. Standalone WebSocket server on port 8765 (with correct handler signature)
2. Tauri overlay should be starting in a new terminal window

This setup bypasses any existing project modules and provides a clean environment
for the overlay to connect to. The WebSocket server sends simulated data to the
overlay UI.

If the Tauri window doesn't open automatically, run:
cd $PWD/overlay && npm install && npm run tauri dev

TO STOP THE SYSTEM:
kill $WS_PID
"

# Keep the script running until Ctrl+C
trap "kill $WS_PID; echo 'System stopped.'" EXIT
wait $WS_PID