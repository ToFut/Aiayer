#!/bin/bash
# Start Perception System
# This script starts all components needed for perception queries to work properly

# Set up color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p logs pids cache/screen_sensor cache/process_sensor cache/file_sensor memory

# Function to check if a process is running
is_running() {
    local pid_file="pids/$1.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# Function to start a process
start_process() {
    local name=$1
    local command=$2
    local log_file="logs/${name}.log"
    
    echo -e "${BLUE}Starting ${name}...${NC}"
    
    # Execute command and save PID
    eval "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "pids/${name}.pid"
    
    # Wait a bit to check if process is still running
    sleep 1
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✓ ${name} started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ ${name} failed to start${NC}"
        return 1
    fi
}

# Function to stop a process
stop_process() {
    local name=$1
    local pid_file="pids/$name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -e "${YELLOW}Stopping ${name} (PID: $pid)...${NC}"
            kill $pid
            sleep 1
            if ps -p $pid > /dev/null; then
                echo -e "${YELLOW}Force stopping ${name}...${NC}"
                kill -9 $pid
            fi
            echo -e "${GREEN}✓ ${name} stopped${NC}"
        else
            echo -e "${YELLOW}✓ ${name} is not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}✓ ${name} is not running (no PID file)${NC}"
    fi
}

# Stop any existing processes
echo -e "\n${BLUE}=== Stopping existing processes ===${NC}"
services=("ws_server" "screen_sensor" "process_sensor" "file_sensor" "memory_connector")
for service in "${services[@]}"; do
    stop_process $service
done

# Initialize memory state if not exists
echo -e "\n${BLUE}=== Initializing memory state ===${NC}"
if [ ! -f "memory/memory_state.json" ]; then
    echo '{
  "version": "1.0",
  "last_update": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "context": {
    "screen_content": ""
  },
  "short_term": [],
  "long_term": [],
  "sensor_data": {
    "screen": {},
    "process": {},
    "file": {}
  }
}' > memory/memory_state.json
    echo -e "${GREEN}✓ Created initial memory state${NC}"
else
    echo -e "${GREEN}✓ Memory state already exists${NC}"
fi

# Pre-populate with screen content
echo -e "\n${BLUE}=== Pre-populating with screen content ===${NC}"
python fix_screen_perception.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Screen content added to memory${NC}"
else
    echo -e "${YELLOW}! Screen content may not have been added${NC}"
fi

# Start WebSocket server
echo -e "\n${BLUE}=== Starting WebSocket server ===${NC}"
start_process "ws_server" "python ws_server_8765.py"
# Wait for the server to initialize
sleep 2

# Verify the server is running
if netstat -an | grep -q "\.8765.*LISTEN"; then
    echo -e "${GREEN}✓ WebSocket server is listening on port 8765${NC}"
else
    echo -e "${RED}✗ WebSocket server is not listening${NC}"
fi

# Start sensors
echo -e "\n${BLUE}=== Starting sensors ===${NC}"
start_process "screen_sensor" "python fixed_screen_sensor.py"
start_process "process_sensor" "python minimal_process_sensor.py"
start_process "file_sensor" "python minimal_file_sensor.py"

# Start memory connector
echo -e "\n${BLUE}=== Starting memory connector ===${NC}"
start_process "memory_connector" "python memory/connect_sensor_to_memory.py"

# Wait for all components to initialize
echo -e "\n${BLUE}=== Waiting for components to initialize (5 seconds) ===${NC}"
for i in {1..5}; do
    echo -n "."
    sleep 1
done
echo ""

# Test if memory has screen content
echo -e "\n${BLUE}=== Verifying memory has screen content ===${NC}"
if grep -q "screen_content" memory/memory_state.json; then
    content_size=$(grep -o '"screen_content":"[^"]*"' memory/memory_state.json | wc -c)
    if [ $content_size -gt 20 ]; then
        echo -e "${GREEN}✓ Memory has screen content ($content_size bytes)${NC}"
    else
        echo -e "${YELLOW}! Memory has minimal screen content${NC}"
    fi
else
    echo -e "${RED}✗ No screen content found in memory${NC}"
fi

# Print status
echo -e "\n${BLUE}=== System Status ===${NC}"
for service in "${services[@]}"; do
    if is_running $service; then
        pid=$(cat "pids/${service}.pid")
        echo -e "${GREEN}✓ ${service} is running (PID: $pid)${NC}"
    else
        echo -e "${RED}✗ ${service} is not running${NC}"
    fi
done

echo -e "\n${GREEN}=== Perception System Started ===${NC}"
echo "The system is now ready for perception queries like 'what am I seeing?'"
echo "To stop the system, run: ./stop_perception_system.sh"
echo -e "${YELLOW}Keep this terminal open while using the system${NC}\n"

# Create stop script if it doesn't exist
if [ ! -f "stop_perception_system.sh" ]; then
    cat > stop_perception_system.sh << 'EOF'
#!/bin/bash
# Stop Perception System

# Set up color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to stop a process
stop_process() {
    local name=$1
    local pid_file="pids/$name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -e "${YELLOW}Stopping ${name} (PID: $pid)...${NC}"
            kill $pid
            sleep 1
            if ps -p $pid > /dev/null; then
                echo -e "${YELLOW}Force stopping ${name}...${NC}"
                kill -9 $pid
            fi
            echo -e "${GREEN}✓ ${name} stopped${NC}"
        else
            echo -e "${YELLOW}✓ ${name} is not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}✓ ${name} is not running (no PID file)${NC}"
    fi
}

# Stop all processes
echo -e "\n${BLUE}=== Stopping perception system ===${NC}"
services=("ws_server" "screen_sensor" "process_sensor" "file_sensor" "memory_connector")
for service in "${services[@]}"; do
    stop_process $service
done

echo -e "\n${GREEN}=== Perception System Stopped ===${NC}\n"
EOF
    chmod +x stop_perception_system.sh
    echo -e "Created stop script: ${YELLOW}stop_perception_system.sh${NC}"
fi