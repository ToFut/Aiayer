#\!/bin/bash
# Start DO Button Server
# This script starts the Ultimate DO Button Server on port 8765

# Create necessary directories
mkdir -p logs/websocket
mkdir -p pids

# Check if a server is already running on port 8765
if lsof -i:8765 -t >/dev/null 2>&1; then
  echo "🔄 Stopping existing WebSocket server on port 8765..."
  lsof -i:8765 -t | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# Start the Ultimate DO Button Server
echo "🚀 Starting Ultimate DO Button Server on port 8765..."
nohup python3 ultimate_do_button_server.py > logs/websocket/ultimate_do_button_server.log 2>&1 &
SERVER_PID=$\!

# Save the PID
echo $SERVER_PID > pids/ultimate_do_button_server.pid
echo "✅ Server started with PID: $SERVER_PID"

# Wait a moment for the server to start
sleep 2

# Verify server is running
if lsof -i:8765 -t >/dev/null 2>&1; then
  echo "✅ Ultimate DO Button Server running on port 8765"
  echo "🔍 View logs: tail -f logs/websocket/ultimate_do_button_server.log"
else
  echo "❌ Failed to start server on port 8765"
  exit 1
fi

echo "🧪 To test the server: python3 test_do_button_fix_verification.py"
