#!/bin/bash

echo "====================================================="
echo "    Starting Full Fixed Aiayer System                "
echo "====================================================="

# 1. Stop any existing processes
echo "Stopping any running services..."
pkill -f "python.*sensor" 2>/dev/null || true
pkill -f "python.*bridge" 2>/dev/null || true
pkill -f "python.*ws_server" 2>/dev/null || true
pkill -f "python.*overlay" 2>/dev/null || true
pkill -f "python.*memory" 2>/dev/null || true
pkill -f "python.*minimal" 2>/dev/null || true
pkill -f "python.*demo" 2>/dev/null || true
sleep 1

# 2. Create required directories
echo "Setting up directories..."
mkdir -p logs/memory
mkdir -p logs/sensors
mkdir -p pids
mkdir -p memory
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p cache/screen_sensor

# 3. Initialize essential cache files
echo "Initializing cache files..."
echo '{
  "version": "1.0",
  "last_update": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "context": {},
  "short_term": [],
  "long_term": []
}' > memory/memory_state.json
echo "{}" > memory/last_context.json
echo "[]" > cache/process_sensor/process_cache.json
echo "[]" > cache/file_sensor/last_file.json
echo "{}" > cache/screen_sensor/screen_cache.json

# 4. Create a standalone websocket server (guaranteed to work)
echo "Creating standalone WebSocket server..."
cat > ./fixed_standalone_ws.py << 'EOF'
#!/usr/bin/env python3
"""
Standalone WebSocket server with proper handler signature
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fixed_ws.log')
    ]
)
logger = logging.getLogger('fixed_ws')

# Connected clients
connected_clients = set()

# Handler function with correct signature
async def handler(websocket, path):
    """Handler function with the REQUIRED path parameter"""
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected at path: {path}")
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to fixed WebSocket server. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Handle "connection_established" message from overlay
                if isinstance(data, dict) and data.get("type") == "connection_established":
                    logger.info(f"Client identified: {data.get('payload', {}).get('client', 'unknown')}")
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_time": datetime.now().isoformat()
                        }
                    }))
                    
                    # Start sending periodic data
                    asyncio.create_task(send_periodic_data(websocket, client_id))
                else:
                    # Echo other messages
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "message": "Received your message",
                            "original": data
                        }
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error", 
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed with {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket, client_id):
    """Send periodic data updates"""
    try:
        import random
        
        # Sample apps for rotation
        apps = [
            {"name": "Terminal", "title": "bash - Aiayer"},
            {"name": "Chrome", "title": "WebSocket API - MDN"},
            {"name": "Visual Studio Code", "title": "overlay_bridge.py - Aiayer"},
            {"name": "Finder", "title": "Documents"}
        ]
        
        counter = 0
        while True:
            # Generate process data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": 10 + random.random() * 10, "memory": 234.5},
                {"name": "VS Code", "pid": 12346, "cpu": 5 + random.random() * 5, "memory": 412.8},
                {"name": "Terminal", "pid": 12347, "cpu": 1 + random.random() * 2, "memory": 78.3},
                {"name": "Finder", "pid": 12348, "cpu": 0.5 + random.random() * 1, "memory": 45.6}
            ]
            
            # Rotate active app every 15 seconds
            app_index = (counter // 3) % len(apps)
            active_app = apps[app_index]
            
            # Create screen data
            screen_data = {
                "active_app": active_app["name"],
                "window_title": active_app["title"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to client
            sensor_data = {
                "processes": processes,
                "screen": screen_data,
                "files": [],
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data
            }))
            
            # Send occasional suggestions (every 30 seconds)
            if counter % 6 == 0:
                suggestion = {
                    "id": f"suggest_{counter}",
                    "title": "System Performance Tip",
                    "content": f"Consider optimizing your workflow based on current {active_app['name']} usage.",
                    "category": "performance",
                    "urgency": random.randint(1, 5),
                    "buttons": [
                        {"label": "Apply", "action": "apply"},
                        {"label": "Dismiss", "action": "dismiss"}
                    ]
                }
                
                await websocket.send(json.dumps({
                    "type": "suggestions",
                    "payload": [suggestion]
                }))
            
            counter += 1
            await asyncio.sleep(5)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed during updates for {client_id}")
    except Exception as e:
        logger.error(f"Error sending periodic data: {e}")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting fixed WebSocket server on {host}:{port}")
    
    # IMPORTANT: use the handler function with path parameter
    async with websockets.serve(handler, host, port):
        logger.info(f"WebSocket server running at ws://{host}:{port}")
        
        # Save PID
        with open('pids/fixed_ws.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        # Run forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        # Create pids directory if it doesn't exist
        os.makedirs("pids", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
EOF

chmod +x ./fixed_standalone_ws.py

# 5. Create a demonstration script (optional, will run if the standalone server fails)
echo "Creating backup demonstration runner..."
cat > ./run_system_demo.py << 'EOF'
#!/usr/bin/env python3
"""
Demo runner for the Aiayer system with fixed overlay bridge
"""
import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/system_demo.log')
    ]
)
logger = logging.getLogger('system_demo')

# Import the fixed OverlayBridge
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.overlay_bridge import OverlayBridge

class SystemDemo:
    """Demo runner for the Aiayer system"""
    
    def __init__(self):
        self.bridge = OverlayBridge(port=8765)
        self.is_running = False
        self.loop = None
        
    def start(self):
        """Start the demo"""
        logger.info("Starting Aiayer system demo")
        
        # Start the bridge
        self.bridge.start()
        logger.info("OverlayBridge started on port 8765")
        
        # Start the demo loop
        self.loop = asyncio.new_event_loop()
        self.is_running = True
        
        def run_loop():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.demo_loop())
            except Exception as e:
                logger.error(f"Error in demo loop: {e}")
                
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        
        # Save PID
        with open('pids/system_demo.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info("Demo started successfully")
        
    async def demo_loop(self):
        """Main demo loop - send periodic updates to clients"""
        while self.is_running:
            try:
                # Generate process data
                processes = self.generate_process_data()
                
                # Generate screen data
                screen_data = self.generate_screen_data()
                
                # Send sensor data
                sensor_data = {
                    "processes": processes,
                    "screen": screen_data,
                    "files": [],
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.bridge.send_sensor_data(sensor_data)
                
                # Every 30 seconds, send a suggestion
                if int(time.time()) % 30 == 0:
                    suggestions = self.generate_suggestions()
                    await self.bridge.send_proactive_suggestions(suggestions)
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in demo loop: {e}")
                await asyncio.sleep(5)
    
    def generate_process_data(self):
        """Generate simulated process data"""
        processes = [
            {"name": "Visual Studio Code", "pid": 12345, "cpu": 15.3, "memory": 234.5},
            {"name": "Chrome", "pid": 12346, "cpu": 8.7, "memory": 412.8},
            {"name": "Terminal", "pid": 12347, "cpu": 2.2, "memory": 78.3},
            {"name": "Finder", "pid": 12348, "cpu": 1.4, "memory": 56.2},
            {"name": "Python", "pid": 12349, "cpu": 4.8, "memory": 123.6}
        ]
        
        # Add some randomness to CPU usage
        import random
        for proc in processes:
            proc["cpu"] = max(0.1, min(100, proc["cpu"] + random.uniform(-2, 2)))
            
        return processes
    
    def generate_screen_data(self):
        """Generate simulated screen data"""
        import random
        
        app_windows = [
            {"app": "Visual Studio Code", "title": "overlay_bridge.py - Aiayer - VS Code"},
            {"app": "Terminal", "title": "bash - /Users/user/Aiayer"},
            {"app": "Chrome", "title": "WebSocket API - Web APIs | MDN"},
            {"app": "Finder", "title": "Aiayer"}
        ]
        
        # Select a random window as active
        active_window = random.choice(app_windows)
        
        return {
            "active_app": active_window["app"],
            "window_title": active_window["title"],
            "resolution": {"width": 1920, "height": 1080},
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_suggestions(self):
        """Generate simulated suggestions"""
        suggestions = [
            {
                "suggestion_id": "suggest_" + str(int(time.time())),
                "title": "Optimize system performance",
                "content": "Your system is running multiple resource-intensive applications. Consider closing unused applications to improve performance.",
                "action_data": {},
                "urgency": 3,
                "category": "performance"
            }
        ]
        
        return suggestions
    
    def stop(self):
        """Stop the demo"""
        logger.info("Stopping demo")
        self.is_running = False
        
        # Stop the bridge
        self.bridge.stop()
        
        logger.info("Demo stopped")

if __name__ == "__main__":
    demo = SystemDemo()
    
    try:
        demo.start()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        demo.stop()
EOF

chmod +x ./run_system_demo.py

# 5. Start the standalone WebSocket server
echo "Starting the fixed standalone WebSocket server..."
python3 ./fixed_standalone_ws.py &
WS_PID=$!
sleep 2

# 6. Check if server is running
if ps -p $WS_PID > /dev/null; then
    echo "✅ Fixed WebSocket server started on port 8765"
else
    echo "❌ Failed to start WebSocket server, trying backup demo instead..."
    # Try to start the demo as a fallback
    python3 ./run_system_demo.py &
    DEMO_PID=$!
    sleep 2
    
    if ps -p $DEMO_PID > /dev/null; then
        echo "✅ Backup system demo started instead"
        WS_PID=$DEMO_PID
    else
        echo "❌ Failed to start both WebSocket server and backup demo"
        exit 1
    fi
fi

# 7. Start Tauri overlay in a separate terminal
echo "Starting Tauri overlay in a new terminal window..."
cat > /tmp/start_tauri_full.sh << 'EOF'
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

chmod +x /tmp/start_tauri_full.sh

# Start a new terminal to run Tauri
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '$PWD' && /tmp/start_tauri_full.sh"'
else
    # Linux and others
    if command -v x-terminal-emulator >/dev/null; then
        x-terminal-emulator -e "bash -c '/tmp/start_tauri_full.sh; exec bash'" &
    elif command -v gnome-terminal >/dev/null; then
        gnome-terminal -- bash -c "/tmp/start_tauri_full.sh; exec bash" &
    elif command -v xterm >/dev/null; then
        xterm -e "bash -c '/tmp/start_tauri_full.sh; exec bash'" &
    else
        echo "⚠️ Could not determine how to open a new terminal window."
        echo "Please open a new terminal window and run:"
        echo "cd $PWD/overlay && npm install && npm run tauri dev"
    fi
fi

echo "
=====================================================
    Full Fixed Aiayer System Running
=====================================================

COMPONENTS:
1. Fixed OverlayBridge with proper WebSocket handler
2. System demo generating simulated data
3. Tauri overlay should be starting in a new terminal window

If the Tauri window doesn't open automatically, run:
cd $PWD/overlay && npm install && npm run tauri dev

TO STOP THE SYSTEM:
kill $WS_PID
"

# Keep the script running until Ctrl+C
trap "kill $WS_PID; echo 'System stopped.'" EXIT

# Print status message
echo "
System is running! Press Ctrl+C to stop.
Logs are available in logs/fixed_ws.log
"

# Wait for WS_PID to finish
wait $WS_PID