#!/bin/bash
# Start the agent workflow system with existing sensors and memory

# Set up colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Agent Workflow System${NC}"
echo -e "${YELLOW}This script starts the complete system with agent workflow integration${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs/agent

# Function to check if a process is running
is_running() {
  if [ -f "pids/$1.pid" ]; then
    pid=$(cat "pids/$1.pid")
    if ps -p $pid > /dev/null; then
      return 0 # Running
    fi
  fi
  return 1 # Not running
}

# Function to start a component
start_component() {
  name=$1
  command=$2
  pidfile="pids/$name.pid"
  
  if is_running $name; then
    echo -e "${YELLOW}$name is already running${NC}"
  else
    echo -e "${GREEN}Starting $name...${NC}"
    mkdir -p pids
    
    # Run the command in the background
    $command > "logs/agent/$name.log" 2>&1 &
    pid=$!
    echo $pid > $pidfile
    
    # Wait to ensure it starts properly
    sleep 2
    
    # Check if it's still running
    if ps -p $pid > /dev/null; then
      echo -e "${GREEN}$name started successfully (PID: $pid)${NC}"
    else
      echo -e "${RED}Failed to start $name${NC}"
      echo -e "${RED}Check logs/agent/$name.log for details${NC}"
    fi
  fi
}

# Start necessary existing components first
echo -e "${BLUE}Step 1: Starting existing sensor components...${NC}"

# Start process sensor
start_component "process_sensor" "python3 fixed_process_sensor.py"

# Start screen sensor
start_component "screen_sensor" "python3 fixed_screen_sensor.py"

# Start memory integration
start_component "memory_integration" "python3 direct_sensor_to_memory.py"

# Wait for sensors to initialize
echo -e "${BLUE}Waiting for sensors to initialize...${NC}"
sleep 3

# Start the agent workflow 
echo -e "${BLUE}Step 2: Starting agent workflow integration...${NC}"

# Start in direct mode (connects directly to the memory system)
start_component "agent_workflow" "python3 agent_workflow/agent_integration.py direct"

echo -e "${GREEN}All components started successfully${NC}"
echo -e "${YELLOW}Monitor logs in the logs/agent/ directory${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all components${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '${RED}Stopping all components...${NC}'; ./stop_agent_workflow.sh; exit 0" INT TERM
while true; do
  sleep 1
done