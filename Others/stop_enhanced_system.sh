#!/bin/bash
# Script to stop the enhanced WebSocket server

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Enhanced WebSocket Server...${NC}"

# Check and kill processes
PIDS_TO_CHECK=("ws_server_8765.pid" "llm_service.pid")

for PID_FILE in "${PIDS_TO_CHECK[@]}"; do
    if [ -f "pids/$PID_FILE" ]; then
        PID=$(cat "pids/$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Killing process from $PID_FILE: $PID${NC}"
            kill -9 $PID 2>/dev/null || true
            echo -e "${GREEN}Process $PID killed.${NC}"
        else
            echo -e "${RED}Process from $PID_FILE ($PID) not running.${NC}"
        fi
        rm "pids/$PID_FILE" 2>/dev/null || true
    else
        echo -e "${RED}PID file $PID_FILE not found.${NC}"
    fi
done

# Additionally, try to find and kill any related processes by name
echo -e "${YELLOW}Checking for other related processes...${NC}"

# Kill Python processes containing 'enhanced_ws_8765.py'
PIDS=$(ps aux | grep "[p]ython.*enhanced_ws_8765.py" | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Killing Python processes for enhanced_ws_8765.py: $PIDS${NC}"
    kill -9 $PIDS 2>/dev/null || true
    echo -e "${GREEN}Processes killed.${NC}"
else
    echo -e "${RED}No enhanced_ws_8765.py processes found.${NC}"
fi

echo -e "${GREEN}System shutdown complete.${NC}"
exit 0