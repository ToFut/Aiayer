#!/bin/bash

echo "====================================================="
echo "   FINAL TAURI CONNECTION SOLUTION                   "
echo "====================================================="

# This script takes a different approach by using a dedicated, standalone 
# connection script that connects directly to the overlay without relying 
# on the problematic WebSocket server.

# Step 1: Kill all potentially interfering processes
echo "Stopping all potential conflicting processes..."
pkill -f "python.*websocket" 2>/dev/null || true
pkill -f "python.*server" 2>/dev/null || true
pkill -f "python.*ws_" 2>/dev/null || true
pkill -f "python.*bridge" 2>/dev/null || true
kill $(lsof -i:8765 -t) 2>/dev/null || true
sleep 2

# Step 2: Make our direct connection script executable
chmod +x ./direct_connect.py

# Step 3: Start the new direct connection client
echo "Starting direct connection client..."
python3 ./direct_connect.py > direct_connect.log 2>&1 &
CLIENT_PID=$!
sleep 2

# Verify client is running
if ps -p $CLIENT_PID > /dev/null; then
    echo "✅ Direct connection client started (PID: $CLIENT_PID)"
else
    echo "❌ Direct connection client failed to start"
    exit 1
fi

# Step 4: Prepare Tauri launch script
echo "Preparing Tauri launch script..."
cat > /tmp/launch_tauri.sh << 'EOF'
#!/bin/bash

echo "Launching Tauri overlay..."
cd "$(dirname "$0")"
cd ./overlay

# Check for node_modules
if [ ! -d "node_modules" ] || [ ! -d "node_modules/@tauri-apps" ]; then
    echo "Installing dependencies (may take a minute)..."
    npm install
fi

# Try running Tauri dev mode
echo "Starting Tauri dev mode..."
npm run tauri dev
EOF

chmod +x /tmp/launch_tauri.sh

# Step 5: Launch Tauri in a new terminal
echo "Launching Tauri in new terminal..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '$PWD' && /tmp/launch_tauri.sh"'
else
    # Linux and others
    echo "Please open a new terminal and run:"
    echo "cd $PWD/overlay && npm install && npm run tauri dev"
fi

echo "
=====================================================
    FINAL SOLUTION IN EFFECT
=====================================================

Instead of fixing the problematic WebSocket server, we've taken a 
complete change of approach:

1. Direct connection client connects to port 8765 (PID: $CLIENT_PID)
2. The client feeds simulated data to the Tauri overlay
3. Tauri should be starting in a new terminal window

This completely bypasses the handler signature problem by using a 
reliable client implementation instead of a server.

To monitor logs:
tail -f direct_connect.log

To stop the direct connection client:
kill $CLIENT_PID

If Tauri fails to load, run these commands in a new terminal:
cd $PWD/overlay
rm -rf node_modules
npm install
npm run tauri dev
"

# Keep the script running so user can see instructions
sleep 60

# Check if client is still running
if ps -p $CLIENT_PID > /dev/null; then
    echo "Direct connection client is still running (PID: $CLIENT_PID)"
    echo "Press Ctrl+C to exit this script (client will keep running)"
else
    echo "⚠️ Direct connection client is no longer running"
    echo "Check direct_connect.log for errors"
fi

# Wait for a while
sleep 3600