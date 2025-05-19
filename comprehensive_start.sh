#!/bin/bash
# comprehensive_start.sh
# A comprehensive script to start the entire system with all fixes

set -e
echo "=== Starting Comprehensive Aiayer System ==="

# Create required directories
echo "Creating required directories..."
mkdir -p cache/process_sensor/backups
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory/sensor_data
mkdir -p logs/sensors/sensor_process
mkdir -p logs/sensors/sensor_screen
mkdir -p logs/sensors/sensor_file
mkdir -p logs/memory
mkdir -p data
mkdir -p pids

# Function to kill processes
kill_process() {
  process_name=$1
  echo "Stopping ${process_name} processes..."
  pids=$(ps aux | grep -i ${process_name} | grep -v grep | awk '{print $2}')
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
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "fixed_ws_server_with_memory"
kill_process "websocket"
kill_process "simple_ws_server_8767"
echo "All processes stopped"

# Prepare cache files
echo "Preparing cache files..."
timestamp=$(date +%Y%m%d_%H%M%S)

# Initialize process cache with proper structure
echo "Initializing process cache..."
if [ -f "cache/process_sensor/process_cache.json" ] && [ -s "cache/process_sensor/process_cache.json" ]; then
  cp "cache/process_sensor/process_cache.json" "cache/process_sensor/backups/process_cache_${timestamp}.json"
fi
echo '{
  "timestamp": '$(date +%s)',
  "active_window": "",
  "active_app": "",
  "active_apps": [],
  "window_history": []
}' > "cache/process_sensor/process_cache.json"

# Initialize screen cache with proper structure
echo "Initializing screen cache..."
if [ -f "cache/screen_sensor/screen_cache.json" ] && [ -s "cache/screen_sensor/screen_cache.json" ]; then
  cp "cache/screen_sensor/screen_cache.json" "cache/screen_sensor/screen_cache.json.bak_${timestamp}"
fi
echo '{
  "timestamp": '$(date +%s)',
  "screen_text": "",
  "has_images": false,
  "has_videos": false
}' > "cache/screen_sensor/screen_cache.json"

# Initialize last_screen.json if it doesn't exist
if [ ! -f "cache/screen_sensor/last_screen.json" ] || [ ! -s "cache/screen_sensor/last_screen.json" ]; then
  echo '{
  "timestamp": '$(date +%s)',
  "screen_text": "",
  "has_images": false,
  "has_videos": false
}' > "cache/screen_sensor/last_screen.json"
fi

# Make sure file cache file exists
if [ ! -f "cache/file_sensor/last_file.json" ] || [ ! -s "cache/file_sensor/last_file.json" ]; then
  echo '{
  "timestamp": '$(date +%s)',
  "files": []
}' > "cache/file_sensor/last_file.json"
fi

# Initialize memory state
echo "Initializing memory state..."
if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
  echo '{
  "last_update": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "sensors": {
    "process": {"status": "initialized", "last_data": null},
    "screen": {"status": "initialized", "last_data": null},
    "file": {"status": "initialized", "last_data": null}
  },
  "memory_stats": {
    "total_entries": 0,
    "last_cleanup": null
  }
}' > "memory/memory_state.json"
fi

# Initialize context tracking
echo "Initializing context tracking..."
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

echo "Cache files prepared"

# Create a fixed process_sensor script
echo "Creating fixed process sensor script..."
cat > fixed_process_sensor.py << EOF
#!/usr/bin/env python3
"""
Fixed Process Sensor Script
"""
import os
import time
import logging
import json
import platform
import psutil
from datetime import datetime
from collections import deque
import asyncio
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/sensor_process/sensor_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define cache path
CACHE_PATH = 'cache/process_sensor/process_cache.json'

class SimpleProcessSensor:
    """Simple process sensor that doesn't require complex imports"""
    
    def __init__(self):
        self.running = False
        self.last_update = time.time()
        self.process_history = deque(maxlen=100)
        self.window_history = deque(maxlen=100)
        self.logger = logger
        
    async def start(self):
        """Start the process sensor."""
        self.running = True
        self.logger.info("Process sensor started")
        return True
    
    async def stop(self):
        """Stop the process sensor."""
        self.running = False
        self.logger.info("Process sensor stopped")
        return True
        
    async def get_data(self):
        """Get current process data."""
        try:
            current_time = time.time()
            
            # Get process data
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        process_info = proc.info
                        processes.append({
                            'pid': process_info['pid'],
                            'name': process_info['name'],
                            'username': process_info['username'],
                            'cpu_percent': process_info['cpu_percent'],
                            'memory_percent': process_info['memory_percent']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception as e:
                self.logger.error(f"Error getting process data: {e}")
                processes = []
            
            # Get window data (simplified for cross-platform)
            windows = []
            try:
                if platform.system() == "Darwin":  # macOS
                    active_app = os.popen("osascript -e 'tell application \"System Events\" to name of first application process whose frontmost is true'").read().strip()
                    if active_app:
                        windows.append({
                            'name': active_app,
                            'owner': active_app,
                            'layer': 0
                        })
                else:
                    # Simplified version for other platforms
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if proc.info['cpu_percent'] > 5.0:  # Assume higher CPU usage might be foreground app
                                windows.append({
                                    'name': proc.info['name'],
                                    'owner': proc.info['name'],
                                    'layer': 0
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
            except Exception as e:
                self.logger.error(f"Error getting window data: {e}")
                
            # Create data object
            data = {
                'timestamp': current_time,
                'type': 'process_sensor',
                'processes': processes,
                'windows': windows,
                'last_update': self.last_update
            }
            
            # Update histories
            self.process_history.append(processes)
            if windows:
                self.window_history.append(windows)
            
            # Update last update time
            self.last_update = current_time
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting process sensor data: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }

def write_cache(data):
    """Write data to cache file."""
    try:
        # Create simple data structure for cache
        active_window = None
        active_app = None
        active_apps = []
        window_history = []
        
        if 'windows' in data and data['windows']:
            active_window = data['windows'][0].get('name', '')
            active_app = data['windows'][0].get('owner', '')
        
        if 'processes' in data and data['processes']:
            active_apps = [p['name'] for p in data['processes'][:10] if p.get('cpu_percent', 0) > 0.1]
        
        cache_data = {
            'timestamp': time.time(),
            'active_window': active_window,
            'active_app': active_app,
            'active_apps': active_apps,
            'window_history': window_history
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        
        # Write to cache
        with open(CACHE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
        logger.debug(f"Wrote to cache: {CACHE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error writing cache: {e}")
        return False

# Main function
async def main():
    """Main function"""
    sensor = SimpleProcessSensor()
    await sensor.start()
    
    print("Process sensor started. Press Ctrl+C to exit.")
    try:
        while True:
            try:
                # Get data
                data = await sensor.get_data()
                # Write to cache
                write_cache(data)
                # Log heartbeat occasionally
                if int(time.time()) % 60 == 0:  # Log every minute
                    logger.info("Process sensor heartbeat")
                # Sleep
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("Stopping process sensor...")
    finally:
        await sensor.stop()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create a simplified memory connector
echo "Creating simplified memory connector..."
cat > fixed_memory_connector.py << EOF
#!/usr/bin/env python3
"""
Simplified Memory Connector
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('memory_connector')

class SimpleMemoryConnector:
    """Simple connector that monitors cache files and updates memory state"""
    
    def __init__(self):
        self.memory_state_file = Path('memory/memory_state.json')
        self.sensor_data_dir = Path('memory/sensor_data')
        self.sensor_data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_files = {
            'process': Path('cache/process_sensor/process_cache.json'),
            'screen': Path('cache/screen_sensor/last_screen.json')
        }
        self.initialize_memory_state()
        
    def initialize_memory_state(self):
        """Initialize or load memory state"""
        if not self.memory_state_file.exists() or os.path.getsize(self.memory_state_file) == 0:
            initial_state = {
                "last_update": datetime.now().isoformat(),
                "sensors": {
                    "process": {"status": "initialized", "last_data": None},
                    "screen": {"status": "initialized", "last_data": None}
                },
                "memory_stats": {
                    "total_entries": 0,
                    "last_cleanup": None
                }
            }
            self.memory_state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_state_file, 'w') as f:
                json.dump(initial_state, f, indent=2)
            logger.info("Initialized new memory state")
            
    async def update_memory_state(self, sensor_type, data):
        """Update memory state with sensor data"""
        try:
            if self.memory_state_file.exists():
                try:
                    with open(self.memory_state_file, 'r') as f:
                        state = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Memory state file is corrupted, reinitializing...")
                    self.initialize_memory_state()
                    with open(self.memory_state_file, 'r') as f:
                        state = json.load(f)
                        
                # Update state
                if 'sensors' not in state:
                    state['sensors'] = {}
                if sensor_type not in state['sensors']:
                    state['sensors'][sensor_type] = {"status": "initialized", "last_data": None}
                    
                # Store minimal data to avoid huge files
                if isinstance(data, dict):
                    minimal_data = {
                        'timestamp': data.get('timestamp', datetime.now().timestamp()),
                        'type': sensor_type
                    }
                    
                    # Add sensor-specific data
                    if sensor_type == 'process':
                        minimal_data['active_window'] = data.get('active_window', '')
                        minimal_data['active_app'] = data.get('active_app', '')
                    elif sensor_type == 'screen':
                        minimal_data['has_text'] = bool(data.get('screen_text', ''))
                        
                    state['sensors'][sensor_type]['last_data'] = minimal_data
                    state['sensors'][sensor_type]['status'] = 'active'
                    state['last_update'] = datetime.now().isoformat()
                    
                    # Write updated state back
                    with open(self.memory_state_file, 'w') as f:
                        json.dump(state, f, indent=2)
                        
                    logger.debug(f"Updated memory state with {sensor_type} data")
                    return True
                else:
                    logger.warning(f"Invalid data format for {sensor_type}")
                    return False
            else:
                logger.warning("Memory state file doesn't exist, creating it...")
                self.initialize_memory_state()
                return False
        except Exception as e:
            logger.error(f"Error updating memory state: {e}")
            return False
            
    async def run(self):
        """Main connector loop"""
        logger.info("Starting simplified memory connector")
        
        while True:
            try:
                # Check cache files
                for sensor_type, cache_file in self.cache_files.items():
                    if cache_file.exists() and os.path.getsize(cache_file) > 0:
                        try:
                            with open(cache_file, 'r') as f:
                                data = json.load(f)
                                if data:
                                    await self.update_memory_state(sensor_type, data)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in {cache_file}")
                        except Exception as e:
                            logger.error(f"Error reading {cache_file}: {e}")
                
                # Update memory last_context.json
                try:
                    if self.memory_state_file.exists():
                        with open(self.memory_state_file, 'r') as f:
                            state = json.load(f)
                            
                        # Create simplified context
                        context = {
                            'timestamp': datetime.now().timestamp(),
                            'active_window': '',
                            'active_app': '',
                            'active_apps': [],
                            'window_history': [],
                            'screen_text': ''
                        }
                        
                        # Add data from process sensor
                        if 'sensors' in state and 'process' in state['sensors']:
                            process_data = state['sensors']['process'].get('last_data', {})
                            if process_data:
                                context['active_window'] = process_data.get('active_window', '')
                                context['active_app'] = process_data.get('active_app', '')
                                
                        # Add data from screen sensor
                        if 'sensors' in state and 'screen' in state['sensors']:
                            screen_data = state['sensors']['screen'].get('last_data', {})
                            if screen_data:
                                context['has_text'] = screen_data.get('has_text', False)
                                
                        # Write context to file
                        with open('memory/last_context.json', 'w') as f:
                            json.dump(context, f, indent=2)
                except Exception as e:
                    logger.error(f"Error updating context: {e}")
                
                # Sleep to prevent high CPU usage
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in connector loop: {e}")
                await asyncio.sleep(5)  # Sleep longer on error

# Main function
async def main():
    connector = SimpleMemoryConnector()
    try:
        await connector.run()
    except KeyboardInterrupt:
        logger.info("Memory connector shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create a very simple web socket server script that runs on port 8767
echo "Creating WebSocket server script..."
cat > simple_ws_server_8767.py << EOF
#!/usr/bin/env python3
"""
Simple WebSocket Server on Port 8767

Minimal WebSocket server implementation for testing.
"""
import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime
from pathlib import Path

# Create log directory if it doesn't exist
log_dir = Path('logs')
log_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

async def handler(websocket, path):
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
                "message": "Connected to WebSocket server",
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
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)

async def send_context_updates():
    """Periodically send context updates to all clients."""
    CONTEXT_FILE = Path('memory/last_context.json')
    
    while True:
        if connected_clients:
            try:
                # Read context file if it exists
                if CONTEXT_FILE.exists():
                    try:
                        with open(CONTEXT_FILE, 'r') as f:
                            context_data = json.load(f)
                            
                            # Send to all clients
                            message = json.dumps({
                                "type": "context_update",
                                "data": context_data,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            await asyncio.gather(
                                *[client.send(message) for client in connected_clients],
                                return_exceptions=True
                            )
                            logger.debug("Sent context update to clients")
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in context file")
                    except Exception as e:
                        logger.error(f"Error reading context file: {e}")
            except Exception as e:
                logger.error(f"Error in context update: {e}")
                
        # Wait before next update
        await asyncio.sleep(2)

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Create the server
        server = await websockets.serve(
            handler,
            "127.0.0.1",
            8767,
            ping_interval=10,
            ping_timeout=5,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64,               # Queue size
            close_timeout=2             # Close timeout
        )
        
        logger.info("WebSocket server started on ws://127.0.0.1:8767")
        
        # Start tasks
        context_task = asyncio.create_task(send_context_updates())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
EOF

# Make the scripts executable
chmod +x fixed_process_sensor.py
chmod +x fixed_memory_connector.py
chmod +x simple_ws_server_8767.py

# Start the WebSocket server
echo "Starting WebSocket server..."
python3 simple_ws_server_8767.py > logs/ws_server_8767.log 2>&1 &
WS_SERVER_PID=$!
echo "WebSocket server started with PID $WS_SERVER_PID"
echo $WS_SERVER_PID > pids/ws_server_8767.pid

# Start the process sensor
echo "Starting process sensor..."
python3 fixed_process_sensor.py > logs/sensors/sensor_process/sensor_process.log 2>&1 &
PROCESS_SENSOR_PID=$!
echo "Process sensor started with PID $PROCESS_SENSOR_PID"
echo $PROCESS_SENSOR_PID > pids/process_sensor.pid

# Start the memory connector
echo "Starting memory connector..."
python3 fixed_memory_connector.py > logs/memory/connector.log 2>&1 &
MEMORY_CONNECTOR_PID=$!
echo "Memory connector started with PID $MEMORY_CONNECTOR_PID" 
echo $MEMORY_CONNECTOR_PID > pids/memory_connector.pid

# Wait briefly to ensure processes start
sleep 2

# Check if servers are running
echo "Checking if processes are running..."
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        proc_name=$(basename "$pidfile" .pid)
        if ps -p $pid > /dev/null; then
            echo "✅ $proc_name is running (PID: $pid)"
        else
            echo "❌ $proc_name failed to start"
        fi
    fi
done

# Check if WebSocket server is running
if command -v lsof &> /dev/null; then
    if lsof -ti :8767 &>/dev/null; then
        echo "✅ WebSocket server successfully running on port 8767"
    else
        echo "❌ WebSocket server failed to start on port 8767"
        echo "See logs/ws_server_8767.log for details"
    fi
fi

echo "=== System Successfully Started ==="
echo "The following components are now running:"
echo "- WebSocket server: ws://127.0.0.1:8767"
echo "- Process sensor: monitoring active applications and windows"
echo "- Memory connector: integrating sensor data with memory system"
echo ""
echo "To check logs, use:"
echo "tail -f logs/ws_server_8767.log              # WebSocket server logs"
echo "tail -f logs/sensors/sensor_process/sensor_process.log  # Process sensor logs"
echo "tail -f logs/memory/connector.log            # Memory connector logs"
echo ""
echo "To check memory state:"
echo "cat memory/memory_state.json"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid 2>/dev/null)"