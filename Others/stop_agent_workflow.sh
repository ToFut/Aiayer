#!/bin/bash
# Stop the agent workflow system and related components

# Set up colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Agent Workflow System${NC}"

# Function to stop a component
stop_component() {
  name=$1
  pidfile="pids/$name.pid"
  
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if ps -p $pid > /dev/null; then
      echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
      kill $pid
      
      # Wait for process to terminate
      for i in {1..5}; do
        if ! ps -p $pid > /dev/null; then
          break
        fi
        sleep 1
      done
      
      # Force kill if still running
      if ps -p $pid > /dev/null; then
        echo -e "${RED}$name did not terminate gracefully, force killing...${NC}"
        kill -9 $pid
      fi
      
      echo -e "${GREEN}$name stopped${NC}"
    else
      echo -e "${YELLOW}$name was not running${NC}"
    fi
    
    # Remove PID file
    rm -f "$pidfile"
  else
    echo -e "${YELLOW}$name was not running (no PID file)${NC}"
  fi
}

# Stop components in reverse order
echo -e "${BLUE}Step 1: Stopping agent workflow...${NC}"
stop_component "agent_workflow"

echo -e "${BLUE}Step 2: Stopping memory and sensor components...${NC}"
stop_component "memory_integration"
stop_component "screen_sensor"
stop_component "process_sensor"

echo -e "${GREEN}All components stopped successfully${NC}"