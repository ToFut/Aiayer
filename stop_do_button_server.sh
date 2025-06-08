#\!/bin/bash
# Stop DO Button Server
# This script stops the Ultimate DO Button Server

# Check if PID file exists
if [ -f pids/ultimate_do_button_server.pid ]; then
  SERVER_PID=$(cat pids/ultimate_do_button_server.pid)
  echo "🛑 Stopping Ultimate DO Button Server (PID: $SERVER_PID)..."
  
  # Stop the server
  kill -9 $SERVER_PID 2>/dev/null || true
  
  # Verify server is stopped
  if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "❌ Failed to stop server with PID: $SERVER_PID"
    exit 1
  else
    echo "✅ Server stopped successfully"
    rm pids/ultimate_do_button_server.pid
  fi
else
  # If PID file doesn't exist, try to find and kill by port
  if lsof -i:8765 -t >/dev/null 2>&1; then
    echo "🛑 Stopping any WebSocket server on port 8765..."
    lsof -i:8765 -t | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Verify port is free
    if lsof -i:8765 -t >/dev/null 2>&1; then
      echo "❌ Failed to free port 8765"
      exit 1
    else
      echo "✅ Port 8765 is now free"
    fi
  else
    echo "ℹ️ No DO Button Server found running on port 8765"
  fi
fi
