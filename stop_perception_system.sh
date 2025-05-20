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
