#!/bin/bash

# Simple System Startup Script
# Starts all system components in proper order

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"

echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting SensAI Complete Integrated System...${NC}"

# Create directories
mkdir -p "$LOG_DIR"/{websocket,backend,memory,sensors,llm,bridge}
mkdir -p "$PID_DIR"
mkdir -p "$SCRIPT_DIR/cache"/{screen_sensor,process_sensor,app_detection,file_sensor,llava_processor}
mkdir -p "$SCRIPT_DIR/results"

# Clean up existing processes
echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] Cleaning up existing processes...${NC}"
pkill -f "fixed_ws_8765" 2>/dev/null || true
pkill -f "enhanced_backend" 2>/dev/null || true
pkill -f "self_contained_llm" 2>/dev/null || true
pkill -f "screen_sensor" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true

# Kill processes on ports
for port in 8765 8766 8767 8080; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}Killing processes on port $port${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

# Clean PID files
rm -f "$PID_DIR"/*.pid
echo "" > "$PID_DIR/components.txt"

sleep 2

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${GREEN}Waiting for $service_name on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if ! lsof -ti :$port >/dev/null 2>&1; then
            sleep 1
            ((attempt++))
        else
            echo -e "${GREEN}$service_name is ready on port $port${NC}"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            echo "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi
    done
    
    echo -e "${RED}$service_name failed to start on port $port${NC}"
    return 1
}

# Start LLM service
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting LLM service...${NC}"
if [ -f "$SCRIPT_DIR/self_contained_llm_ws.py" ]; then
    nohup python3 "$SCRIPT_DIR/self_contained_llm_ws.py" > "$LOG_DIR/llm/llm_service.log" 2>&1 &
    pid=$!
    echo $pid > "$PID_DIR/llm_service.pid"
    echo "llm_service:$pid" >> "$PID_DIR/components.txt"
    
    if wait_for_service "LLM service" 8766; then
        echo -e "${GREEN}LLM service started successfully (PID: $pid)${NC}"
    else
        echo -e "${RED}Failed to start LLM service${NC}"
        exit 1
    fi
else
    echo -e "${RED}LLM service file not found${NC}"
    exit 1
fi

sleep 2

# Start backend server
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting backend server...${NC}"
if [ -f "$SCRIPT_DIR/enhanced_backend_server.py" ]; then
    nohup python3 "$SCRIPT_DIR/enhanced_backend_server.py" > "$LOG_DIR/backend/backend_server.log" 2>&1 &
    pid=$!
    echo $pid > "$PID_DIR/backend_server.pid"
    echo "backend_server:$pid" >> "$PID_DIR/components.txt"
    
    if wait_for_service "Backend server" 8765; then
        echo -e "${GREEN}Backend server started successfully (PID: $pid)${NC}"
    else
        echo -e "${RED}Failed to start backend server${NC}"
        exit 1
    fi
else
    echo -e "${RED}Backend server file not found${NC}"
    exit 1
fi

sleep 2

# Start WebSocket server
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting WebSocket server...${NC}"
if [ -f "$SCRIPT_DIR/fixed_ws_8765.py" ]; then
    nohup python3 "$SCRIPT_DIR/fixed_ws_8765.py" > "$LOG_DIR/websocket/ws_server.log" 2>&1 &
    pid=$!
    echo $pid > "$PID_DIR/ws_server.pid"
    echo "ws_server:$pid" >> "$PID_DIR/components.txt"
    
    # WebSocket server uses same port as backend, so we don't wait for a different port
    echo -e "${GREEN}WebSocket server started successfully (PID: $pid)${NC}"
else
    echo -e "${RED}WebSocket server file not found${NC}"
    exit 1
fi

sleep 2

# Start process sensor
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting process sensor...${NC}"
if [ -f "$SCRIPT_DIR/sensors/process_sensor.py" ]; then
    cat > "$SCRIPT_DIR/run_process_sensor.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sensors.process_sensor import ProcessSensor

async def main():
    config = {
        'interval_sec': 5,
        'exclude_patterns': ['kernel', 'system', 'daemon']
    }
    
    sensor = ProcessSensor(config)
    if await sensor.start():
        print("Process sensor started successfully")
        # Keep running
        while True:
            await asyncio.sleep(1)
    else:
        print("Failed to start process sensor")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    nohup python3 "$SCRIPT_DIR/run_process_sensor.py" > "$LOG_DIR/sensors/process_sensor.log" 2>&1 &
    pid=$!
    echo $pid > "$PID_DIR/process_sensor.pid"
    echo "process_sensor:$pid" >> "$PID_DIR/components.txt"
    echo -e "${GREEN}Process sensor started (PID: $pid)${NC}"
else
    echo -e "${YELLOW}Process sensor not found, skipping${NC}"
fi

# Start screen sensor
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting screen sensor...${NC}"
if [ -f "$SCRIPT_DIR/sensors/screen_sensor.py" ]; then
    cat > "$SCRIPT_DIR/run_screen_sensor.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sensors.screen_sensor import ScreenSensor

async def main():
    config = {
        'interval_sec': 3,
        'max_memory_mb': 50
    }
    
    sensor = ScreenSensor(config)
    if await sensor.initialize():
        sensor.start()
        print("Screen sensor started successfully")
        # Keep running
        while True:
            await asyncio.sleep(1)
    else:
        print("Failed to start screen sensor")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    nohup python3 "$SCRIPT_DIR/run_screen_sensor.py" > "$LOG_DIR/sensors/screen_sensor.log" 2>&1 &
    pid=$!
    echo $pid > "$PID_DIR/screen_sensor.pid"
    echo "screen_sensor:$pid" >> "$PID_DIR/components.txt"
    echo -e "${GREEN}Screen sensor started (PID: $pid)${NC}"
else
    echo -e "${YELLOW}Screen sensor not found, skipping${NC}"
fi

# Start overlay HTTP server
echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Starting overlay server...${NC}"
cd "$SCRIPT_DIR"
nohup python3 -m http.server 8080 > "$LOG_DIR/bridge/overlay_server.log" 2>&1 &
pid=$!
echo $pid > "$PID_DIR/overlay_server.pid"
echo "overlay_server:$pid" >> "$PID_DIR/components.txt"
echo -e "${GREEN}Overlay server started on port 8080 (PID: $pid)${NC}"

sleep 3

# Create stop script
cat > "$SCRIPT_DIR/stop_system.sh" << 'EOF'
#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"

echo -e "${GREEN}Stopping system components...${NC}"

# Stop by PID files
if [ -f "$PID_DIR/components.txt" ]; then
    while IFS=: read -r component pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Stopping $component (PID: $pid)${NC}"
            kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        fi
    done < "$PID_DIR/components.txt"
fi

# Kill by PID files
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        fi
        rm -f "$pid_file"
    fi
done

# Kill by port
for port in 8765 8766 8767 8080; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo -e "${GREEN}Killing processes on port $port${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

# Kill by process pattern
pkill -f "fixed_ws_8765" 2>/dev/null || true
pkill -f "enhanced_backend" 2>/dev/null || true
pkill -f "self_contained_llm" 2>/dev/null || true
pkill -f "screen_sensor" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true

echo -e "${GREEN}System stopped${NC}"
EOF

chmod +x "$SCRIPT_DIR/stop_system.sh"

# Display system status
echo
echo -e "${GREEN}=== SensAI System Started Successfully ===${NC}"
echo
echo -e "${GREEN}Running Components:${NC}"
if [ -f "$PID_DIR/components.txt" ]; then
    while IFS=: read -r component pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "  ✅ $component (PID: $pid)"
        else
            echo -e "  ❌ $component (PID: $pid - not running)"
        fi
    done < "$PID_DIR/components.txt"
fi

echo
echo -e "${GREEN}Service Endpoints:${NC}"
echo -e "  🌐 WebSocket Server: ws://localhost:8765"
echo -e "  🤖 LLM Service: ws://localhost:8766" 
echo -e "  📱 System Dashboard: http://localhost:8080/system_dashboard.html"
echo -e "  💬 Chat Interface: http://localhost:8080/futuristic_overlay.html"

echo
echo -e "${GREEN}Log Files:${NC}"
echo -e "  📄 WebSocket: $LOG_DIR/websocket/ws_server.log"
echo -e "  📄 Backend: $LOG_DIR/backend/backend_server.log"
echo -e "  📄 LLM: $LOG_DIR/llm/llm_service.log"
echo -e "  📄 Sensors: $LOG_DIR/sensors/"

echo
echo -e "${GREEN}Control Commands:${NC}"
echo -e "  🛑 Stop System: ./stop_system.sh"
echo -e "  📊 Monitor Logs: tail -f $LOG_DIR/websocket/ws_server.log"
echo -e "  🔍 Check Status: ps aux | grep -E '(fixed_ws|enhanced_backend|self_contained)'"

echo
echo -e "${GREEN}🎉 System startup completed! Access the dashboard at:${NC}"
echo -e "${YELLOW}http://localhost:8080/system_dashboard.html${NC}"
echo
echo -e "${GREEN}Press Ctrl+C to monitor or run './stop_system.sh' to stop the system${NC}"

# Monitor mode
trap 'echo -e "\n${GREEN}To stop the system, run: ./stop_system.sh${NC}"; exit 0' INT

# Keep script running and show status
while true; do
    sleep 30
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] System running... (Press Ctrl+C to exit monitor)${NC}"
done