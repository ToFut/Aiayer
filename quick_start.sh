#!/bin/bash
# quick_start.sh
# A minimal script to start just the memory connector and WebSocket server

set -e
echo "=== Starting QuickStart System ==="

# Create required directories
mkdir -p memory logs/memory pids

# Create essential files if they don't exist
if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
  echo "{\"last_update\": \"$(date -Iseconds)\"}" > "memory/memory_state.json"
fi

if [ ! -f "memory/last_context.json" ] || [ ! -s "memory/last_context.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "memory/last_context.json"
fi

# Function to kill processes
kill_process() {
  process_name=$1
  echo "Stopping ${process_name} processes..."
  pids=$(ps aux | grep -i "${process_name}" | grep -v grep | awk '{print $2}')
  if [ -n "$pids" ]; then
    echo "Killing processes: $pids"
    for pid in $pids; do
      kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
    done
    echo "${process_name} processes stopped"
  else
    echo "No ${process_name} processes found running"
  fi
}

# Stop any running processes
echo "Stopping any running processes..."
kill_process "fixed_memory_connector"
kill_process "fixed_ws_server"

# Check for processes using port 8767
if command -v lsof &> /dev/null; then
  pid=$(lsof -ti :8767 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "Killing process $pid using port 8767"
    kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
    sleep 1
  fi
fi

# Create minimal memory connector
cat > quick_memory_connector.py << 'EOF'
#!/usr/bin/env python3
import json
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/quick_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Save PID
with open('pids/quick_connector.pid', 'w') as f:
    f.write(str(os.getpid()))

# Main loop
while True:
    try:
        # Update memory state timestamp
        memory_state = {"last_update": datetime.now().isoformat()}
        with open('memory/memory_state.json', 'w') as f:
            json.dump(memory_state, f, indent=2)
        
        # Update context timestamp
        context = {"timestamp": int(time.time())}
        with open('memory/last_context.json', 'w') as f:
            json.dump(context, f, indent=2)
        
        logger.info("Updated memory files")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(5)
EOF

# Create minimal WebSocket server
cat > quick_ws_server.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import json
import logging
import websockets
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/quick_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

async def handler(websocket):
    """Handle WebSocket connections."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to Quick WebSocket server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except Exception as e:
        logger.error(f"Connection error: {e}")
    finally:
        connected_clients.remove(websocket)

async def main():
    # Save PID
    with open('pids/quick_ws_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Create server
    async with websockets.serve(handler, "127.0.0.1", 8767):
        logger.info("QuickStart WebSocket server running on ws://127.0.0.1:8767")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
EOF

# Make scripts executable
chmod +x quick_memory_connector.py
chmod +x quick_ws_server.py

# Start memory connector
echo "Starting memory connector..."
python3 quick_memory_connector.py > logs/memory/quick_connector.log 2>&1 &
CONNECTOR_PID=$!
echo $CONNECTOR_PID > pids/quick_connector.pid
echo "Memory connector started with PID $CONNECTOR_PID"

# Wait for connector to initialize
sleep 2

# Start WebSocket server
echo "Starting WebSocket server..."
python3 quick_ws_server.py > logs/memory/quick_ws_server.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/quick_ws_server.pid
echo "WebSocket server started with PID $WS_SERVER_PID"

# Wait for server to initialize
sleep 2

# Verify services are running
echo "Verifying services..."
for pid_file in pids/quick_*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        service_name=$(basename "$pid_file" .pid)
        if ps -p $pid > /dev/null; then
            echo "✅ Service $service_name is running (PID: $pid)"
        else
            echo "❌ Service $service_name failed to start"
        fi
    fi
done

# Verify WebSocket server
if command -v lsof &> /dev/null; then
    if lsof -ti :8767 &>/dev/null; then
        echo "✅ WebSocket server successfully running on port 8767"
    else
        echo "❌ WebSocket server failed to start on port 8767"
    fi
fi

echo "=== QuickStart System Started ==="
echo "Connect to WebSocket server at: ws://127.0.0.1:8767"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/quick_*.pid 2>/dev/null)"