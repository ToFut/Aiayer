#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Stopping Real DO Button System...${NC}"
echo -e "${BLUE}====================================${NC}"

# Directory where PID files are stored
PID_DIR="pids"

# Function to check if a process is running and stop it
stop_process() {
    local pid_file="$PID_DIR/$1"
    local process_name="$2"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Stopping $process_name (PID: $PID)...${NC}"
            kill -15 $PID
            sleep 1
            
            # Check if process is still running
            if ps -p $PID > /dev/null; then
                echo -e "${RED}Process still running, sending SIGKILL...${NC}"
                kill -9 $PID
                sleep 1
            fi
            
            # Final check
            if ! ps -p $PID > /dev/null; then
                echo -e "${GREEN}$process_name stopped successfully${NC}"
                rm "$pid_file"
            else
                echo -e "${RED}Failed to stop $process_name${NC}"
            fi
        else
            echo -e "${YELLOW}$process_name is not running (PID: $PID)${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}No PID file found for $process_name${NC}"
    fi
}

# Stop all system components
stop_process "real_do_button_executor.pid" "Real DO Button Executor"
stop_process "enhanced_enterprise_backend.pid" "Enhanced Enterprise Backend"
stop_process "process_sensor.pid" "Process Sensor"
stop_process "total_screen_analyzer.pid" "Total Screen Analyzer"
stop_process "smart_memory_feeder.pid" "Smart Memory Feeder"
stop_process "memory_trigger_connector.pid" "Memory Trigger Connector"
stop_process "memory_trigger_websocket.pid" "Memory Trigger WebSocket"

# Check for any stray websocket servers on our ports
check_port() {
    local port="$1"
    local process_name="$2"
    
    # Get PID of process using this port
    local port_pid=$(lsof -i:$port -t 2>/dev/null)
    
    if [ -n "$port_pid" ]; then
        echo -e "${YELLOW}Found stray $process_name on port $port (PID: $port_pid)${NC}"
        echo -e "${YELLOW}Stopping process...${NC}"
        kill -15 $port_pid
        sleep 1
        
        # Check if still running
        if lsof -i:$port -t &>/dev/null; then
            echo -e "${RED}Process still using port $port, sending SIGKILL...${NC}"
            kill -9 $(lsof -i:$port -t)
            sleep 1
        fi
        
        # Final check
        if ! lsof -i:$port -t &>/dev/null; then
            echo -e "${GREEN}Port $port is now free${NC}"
        else
            echo -e "${RED}Failed to free port $port${NC}"
        fi
    else
        echo -e "${GREEN}Port $port is free${NC}"
    fi
}

# Check both primary ports
check_port "8765" "WebSocket Server"
check_port "8767" "Backend Server"

# Final status check
echo -e "\n${BLUE}===========================${NC}"
echo -e "${BLUE}System Shutdown Complete${NC}"
echo -e "${BLUE}===========================${NC}"

# Show any remaining Python processes (optional)
echo -e "\n${YELLOW}Checking for remaining related Python processes:${NC}"
ps aux | grep -E 'real_do_button|enhanced_enterprise_backend|process_sensor|screen_analyzer|smart_memory_feeder' | grep -v grep

echo -e "\n${GREEN}System shutdown completed${NC}"