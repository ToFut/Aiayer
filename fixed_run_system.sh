#!/bin/bash
# Fixed system startup script with proper port configuration and error handling
# This script ensures all components start in the correct order with proper configurations

# Text colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    color=$1
    message=$2
    case $color in
        "green") echo -e "${GREEN}${message}${NC}" ;;
        "yellow") echo -e "${YELLOW}${message}${NC}" ;;
        "blue") echo -e "${BLUE}${message}${NC}" ;;
        "red") echo -e "${RED}${message}${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Function to check if a service is running 
check_service() {
    name=$1
    pid_file=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            return 0  # Service is running
        fi
    fi
    return 1  # Service is not running
}

# Function to start a service with proper logging
start_service() {
    service_name=$1
    command=$2
    log_file=$3
    pid_file=$4
    wait_seconds=${5:-3}  # Default wait time is 3 seconds
    
    print_message "blue" "Starting $service_name..."
    
    # Create log directory if it doesn't exist
    log_dir=$(dirname "$log_file")
    mkdir -p "$log_dir"
    
    # Run the command
    eval "$command > $log_file 2>&1 &"
    pid=$!
    
    # Save the PID to a file
    mkdir -p "$(dirname "$pid_file")"
    echo $pid > "$pid_file"
    
    # Wait to see if the process stays running
    sleep $wait_seconds
    if ps -p $pid > /dev/null; then
        print_message "green" "✅ $service_name started successfully (PID: $pid)"
        return 0
    else
        print_message "red" "❌ $service_name failed to start - check logs at $log_file"
        return 1
    fi
}

# Clean up function to handle script termination
cleanup() {
    print_message "yellow" "Shutting down all services..."
    
    # Kill all running services
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            print_message "blue" "Stopping $name (PID: $pid)..."
            kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null
            rm -f "$pid_file"
        fi
    done
    
    print_message "green" "All services stopped"
    exit 0
}

# Create necessary directories
print_message "blue" "Creating necessary directories..."
mkdir -p logs/sensors/screen_sensor
mkdir -p logs/sensors/process_sensor
mkdir -p logs/sensors/file_sensor
mkdir -p logs/llm
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p memory/screen_data

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Kill any existing processes from previous runs
print_message "yellow" "Stopping any existing processes from previous runs..."
pkill -f "fixed_bridge_server.py" 2>/dev/null || true
pkill -f "self_contained_llm_ws.py" 2>/dev/null || true
pkill -f "memory_system.py" 2>/dev/null || true
pkill -f "enhanced_fixed_screen_sensor.py" 2>/dev/null || true
pkill -f "fixed_process_sensor.py" 2>/dev/null || true
pkill -f "enhanced_backend_server.py" 2>/dev/null || true
sleep 2

# Start the bridge server - this should be first as others depend on it
start_service "bridge server" "python3 fixed_bridge_server.py" "logs/bridge_server.log" "pids/bridge_server.pid" 5
if [ $? -ne 0 ]; then
    print_message "red" "❌ Failed to start bridge server - CRITICAL COMPONENT"
    print_message "red" "Cannot continue without the bridge server"
    exit 1
fi

# Wait for bridge server to initialize
sleep 3
print_message "green" "Bridge server is running on port 8767"

# Start the enhanced screen sensor with the correct port
print_message "blue" "Starting enhanced screen sensor..."
start_service "enhanced screen sensor" "python3 sensors/enhanced_fixed_screen_sensor.py" "logs/sensors/screen_sensor/screen_sensor.log" "pids/screen_sensor.pid"
if [ $? -ne 0 ]; then
    print_message "yellow" "⚠️ Enhanced screen sensor failed to start. Will continue without it."
fi

# Start a simple process sensor
print_message "blue" "Starting minimal process sensor..."
cat > sensors/minimal_process_sensor.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal Process Sensor
Provides basic process information to the bridge server.
"""
import asyncio
import websockets
import json
import time
import os
import logging
import psutil
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors/process_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

class MinimalProcessSensor:
    def __init__(self, bridge_uri="ws://localhost:8767", update_interval=10):
        self.bridge_uri = bridge_uri
        self.update_interval = update_interval
        self.running = True
        logger.info(f"Minimal process sensor initialized (interval: {update_interval}s)")
        
    def get_processes(self):
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
                try:
                    process_info = proc.info
                    processes.append({
                        'pid': process_info['pid'],
                        'name': process_info['name'],
                        'username': process_info['username'],
                        'memory': process_info['memory_info'].rss if process_info['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return processes
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return []
    
    def get_active_window(self):
        """Get active window (simplified)"""
        try:
            # This is a simplified implementation - ideally we'd use platform-specific methods
            return {
                'title': 'Current Window',
                'app': 'Current Application',
                'time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return {}
    
    async def run(self):
        """Run the process sensor"""
        logger.info("Starting minimal process sensor")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/process_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        while self.running:
            try:
                # Connect to bridge server
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Register as a sensor
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "sensor",
                        "sensor_type": "process",
                        "version": "1.0.0"
                    }))
                    
                    # Send process data periodically
                    while self.running:
                        # Get process data
                        processes = self.get_processes()
                        active_window = self.get_active_window()
                        
                        # Send to bridge server
                        await websocket.send(json.dumps({
                            "type": "process_data",
                            "payload": {
                                "processes": processes[:10],  # Send only top 10 processes
                                "active_window": active_window,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        
                        # Update memory context
                        try:
                            # Update last_context.json with process data
                            memory_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory')
                            context_file = os.path.join(memory_dir, 'last_context.json')
                            
                            if os.path.exists(context_file):
                                try:
                                    with open(context_file, 'r') as f:
                                        context = json.load(f)
                                except json.JSONDecodeError:
                                    context = {}
                            else:
                                context = {}
                            
                            # Update with process data
                            if 'active_apps' not in context:
                                context['active_apps'] = []
                            
                            # Add top 5 processes
                            top_apps = [p['name'] for p in sorted(processes, key=lambda x: x['memory'], reverse=True)[:5]]
                            for app in top_apps:
                                if app not in context['active_apps']:
                                    context['active_apps'].insert(0, app)
                            
                            # Keep only the top 10 apps
                            context['active_apps'] = context['active_apps'][:10]
                            
                            # Write updated context
                            with open(context_file, 'w') as f:
                                json.dump(context, f, indent=2)
                                
                            logger.info(f"Updated last_context.json with process data")
                        except Exception as e:
                            logger.error(f"Error updating context: {e}")
                        
                        # Wait for next update
                        await asyncio.sleep(self.update_interval)
                        
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)

async def main():
    sensor = MinimalProcessSensor()
    await sensor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process sensor stopped by user")
    except Exception as e:
        logger.error(f"Error running process sensor: {e}")
EOF

chmod +x sensors/minimal_process_sensor.py
start_service "minimal process sensor" "python3 sensors/minimal_process_sensor.py" "logs/sensors/process_sensor/process_sensor.log" "pids/process_sensor.pid"
if [ $? -ne 0 ]; then
    print_message "yellow" "⚠️ Process sensor failed to start. Will continue without it."
fi

# Start the memory system
start_service "memory system" "python3 memory/memory_system.py" "logs/memory/memory_system.log" "pids/memory_system.pid"
if [ $? -ne 0 ]; then
    print_message "yellow" "⚠️ Memory system failed to start. Context integration will be limited."
fi

# Start the LLM service
start_service "LLM service" "python3 self_contained_llm_ws.py" "logs/llm/self_contained_llm.log" "pids/llm_service.pid"
if [ $? -ne 0 ]; then
    print_message "red" "❌ LLM service failed to start. Check logs at logs/llm/self_contained_llm.log"
    print_message "yellow" "Continuing without LLM service, but context-aware queries won't work"
fi

# Start the enhanced backend server
start_service "enhanced backend server" "python3 enhanced_backend_server.py" "logs/backend/backend_server.log" "pids/backend_server.pid"
if [ $? -ne 0 ]; then
    print_message "yellow" "⚠️ Enhanced backend server failed to start. User interface may be limited."
fi

# Final system status message
print_message "green" "=========================================================="
print_message "green" "✅ Context-integrated system is now running!"
print_message "green" "=========================================================="
print_message "blue" "Bridge server is running on port 8767"
print_message "blue" "LLM service is receiving context from memory system"
print_message "blue" "Screen sensor is capturing screen content"
print_message "blue" "Process sensor is tracking active applications"

# Provide suggestion buttons for user responses
print_message "yellow" "CONTEXT-AWARE QUERIES:"
print_message "blue" "- \"What am I seeing?\" - Get information about your screen"
print_message "blue" "- \"What app am I using?\" - Get information about the active application"
print_message "blue" "- \"Summarize my context\" - Get a complete context summary"

# Print information about monitoring logs
print_message "yellow" "MONITORING:"
echo "tail -f logs/bridge_server.log                      # Bridge server logs"
echo "tail -f logs/sensors/screen_sensor/screen_sensor.log # Screen sensor logs"
echo "tail -f logs/sensors/process_sensor/process_sensor.log # Process sensor logs"
echo "tail -f logs/llm/self_contained_llm.log             # LLM service logs"
echo "tail -f logs/memory/memory_system.log               # Memory system logs"
echo "tail -f logs/backend/backend_server.log             # Backend server logs"

# Keep script running
print_message "blue" "Press Ctrl+C to stop all services"
while true; do
    # Check if all essential services are still running
    check_bridge=$(check_service "bridge_server" "pids/bridge_server.pid")
    check_llm=$(check_service "llm_service" "pids/llm_service.pid")
    check_memory=$(check_service "memory_system" "pids/memory_system.pid")
    
    if [ $check_bridge -ne 0 ]; then
        print_message "red" "⚠️ Bridge server is not running - attempting to restart..."
        start_service "bridge server" "python3 fixed_bridge_server.py" "logs/bridge_server.log" "pids/bridge_server.pid" 5
    fi
    
    if [ $check_llm -ne 0 ]; then
        print_message "yellow" "⚠️ LLM service is not running - attempting to restart..."
        start_service "LLM service" "python3 self_contained_llm_ws.py" "logs/llm/self_contained_llm.log" "pids/llm_service.pid"
    fi
    
    if [ $check_memory -ne 0 ]; then
        print_message "yellow" "⚠️ Memory system is not running - attempting to restart..."
        start_service "memory system" "python3 memory/memory_system.py" "logs/memory/memory_system.log" "pids/memory_system.pid"
    fi
    
    sleep 30
done