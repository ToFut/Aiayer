#!/bin/bash
# absolute_final_fixed_system.sh
# A minimal but working version of the system that ensures all core components run

set -e
echo "=== Starting Absolute Final Fixed System ==="

# Create essential directories
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs
mkdir -p pids

# Kill any processes that might be in the way
echo "Cleaning up any existing processes..."
for port in 8767 8765; do
  pid=$(lsof -ti :$port 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "Killing process $pid using port $port"
    kill -9 $pid 2>/dev/null || echo "Failed to kill process $pid"
    sleep 1
  fi
done

# Kill any existing Python processes from previous runs
ps aux | grep -E "python3.*minimal_ws|sensor|memory_connector" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "Environment cleaned"

# Create essential files if they don't exist
echo "Creating essential files..."
if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
  echo '{"last_update": "'$(date -Iseconds)'"}' > "memory/memory_state.json"
fi

if [ ! -f "memory/last_context.json" ] || [ ! -s "memory/last_context.json" ]; then
  echo '{
    "timestamp": '$(date +%s)',
    "active_window": "",
    "active_app": "",
    "active_apps": [],
    "window_history": [],
    "screen_text": ""
  }' > "memory/last_context.json"
fi

# Create a simple memory updater that just updates the timestamp
cat > memory_updater.py << 'EOF'
#!/usr/bin/env python3
"""
Simple memory state updater that just updates the timestamp
"""
import json
import os
import time
import sys
from datetime import datetime

# Create necessary directories
os.makedirs("memory", exist_ok=True)
os.makedirs("pids", exist_ok=True)

# Save PID
with open("pids/memory_updater.pid", "w") as f:
    f.write(str(os.getpid()))

print("Memory updater started")

# Main loop
try:
    while True:
        # Update memory state
        try:
            # Load current state or create new
            try:
                with open("memory/memory_state.json", "r") as f:
                    state = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                state = {}
            
            # Update timestamp
            state["last_update"] = datetime.now().isoformat()
            
            # Save updated state
            with open("memory/memory_state.json", "w") as f:
                json.dump(state, f, indent=2)
                
            # Also update last context
            try:
                with open("memory/last_context.json", "r") as f:
                    context = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                context = {
                    "active_window": "",
                    "active_app": "",
                    "active_apps": [],
                    "window_history": [],
                    "screen_text": ""
                }
            
            # Update timestamp
            context["timestamp"] = int(time.time())
            
            # Save updated context
            with open("memory/last_context.json", "w") as f:
                json.dump(context, f, indent=2)
                
            print(f"Memory updated: {datetime.now().isoformat()}")
        except Exception as e:
            print(f"Error updating memory: {e}")
        
        # Sleep for a while
        time.sleep(5)
except KeyboardInterrupt:
    print("Memory updater stopped by user")
except Exception as e:
    print(f"Memory updater error: {e}")
    sys.exit(1)
EOF

# Create a minimal WebSocket server that actually works
cat > minimal_ws_server_8767.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal WebSocket Server on port 8767
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Try to import websockets
try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Create directories
os.makedirs("pids", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Save PID
with open("pids/ws_server_8767.pid", "w") as f:
    f.write(str(os.getpid()))

print(f"Starting WebSocket server on port 8767...")

# Handler for WebSocket connections
async def handler(websocket):
    print(f"Client connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to WebSocket server on port 8767",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process incoming messages
        async for message in websocket:
            print(f"Received: {message}")
            
            # Try to parse JSON
            try:
                data = json.loads(message)
                
                # Check if this is a memory request
                if isinstance(data, dict) and data.get("type") == "get_memory":
                    try:
                        # Read memory state
                        with open("memory/memory_state.json", "r") as f:
                            memory_state = json.load(f)
                            
                        # Send memory state
                        await websocket.send(json.dumps({
                            "type": "memory_state",
                            "data": memory_state,
                            "timestamp": datetime.now().isoformat()
                        }))
                    except Exception as e:
                        print(f"Error reading memory: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"Error reading memory: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }))
                else:
                    # Echo back the JSON data
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                # Echo back as plain text for non-JSON messages
                await websocket.send(f"Echo: {message}")
                
    except Exception as e:
        print(f"Error in handler: {e}")

async def main():
    # Start the WebSocket server
    async with websockets.serve(handler, "localhost", 8767):
        print(f"WebSocket server running on ws://localhost:8767")
        
        # Keep running forever
        await asyncio.Future()

# Main entry point
if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
EOF

# Make the scripts executable
chmod +x memory_updater.py
chmod +x minimal_ws_server_8767.py

# Start the memory updater
echo "Starting memory updater..."
python3 memory_updater.py > logs/memory_updater.log 2>&1 &
MEMORY_UPDATER_PID=$!
echo $MEMORY_UPDATER_PID > pids/memory_updater.pid
echo "Memory updater started with PID $MEMORY_UPDATER_PID"

# Wait a moment for memory updater to initialize
sleep 2

# Check if memory updater is running
if ps -p $MEMORY_UPDATER_PID > /dev/null; then
    echo "✅ Memory updater is running"
else
    echo "❌ Memory updater failed to start"
    cat logs/memory_updater.log
    exit 1
fi

# Start the WebSocket server
echo "Starting WebSocket server on port 8767..."
python3 minimal_ws_server_8767.py > logs/ws_server_8767.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/ws_server_8767.pid
echo "WebSocket server started with PID $WS_SERVER_PID"

# Wait a moment for WebSocket server to initialize
sleep 2

# Check if WebSocket server is running
if ps -p $WS_SERVER_PID > /dev/null; then
    echo "✅ WebSocket server is running"
else
    echo "❌ WebSocket server failed to start"
    cat logs/ws_server_8767.log
    exit 1
fi

# Check if port 8767 is being listened on
if command -v lsof &> /dev/null; then
    if lsof -ti :8767 &>/dev/null; then
        echo "✅ Port 8767 is open and listening"
    else
        echo "❌ Port 8767 is not being listened on"
        exit 1
    fi
fi

echo "=== System Started Successfully ==="
echo "The system is now running with the following components:"
echo "- Memory updater (PID: $MEMORY_UPDATER_PID)"
echo "- WebSocket server on port 8767 (PID: $WS_SERVER_PID)"
echo ""
echo "Connect to WebSocket server at: ws://localhost:8767"
echo ""
echo "To check logs:"
echo "- tail -f logs/memory_updater.log     # Memory updater logs"
echo "- tail -f logs/ws_server_8767.log     # WebSocket server logs"
echo ""
echo "To stop the system:"
echo "- kill $MEMORY_UPDATER_PID $WS_SERVER_PID"
echo "- or: kill \$(cat pids/*.pid 2>/dev/null)"