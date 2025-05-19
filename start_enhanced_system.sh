#!/bin/bash
# Script to start the enhanced WebSocket server with memory integration

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Enhanced WebSocket Server with Memory and Advanced LLM Integration...${NC}"

# Create required directories
mkdir -p logs pids

# Step 1: Kill any existing processes
echo -e "${YELLOW}Checking for existing processes...${NC}"
PIDS_TO_CHECK=("ws_server_8765.pid" "llm_service.pid")

for PID_FILE in "${PIDS_TO_CHECK[@]}"; do
    if [ -f "pids/$PID_FILE" ]; then
        PID=$(cat "pids/$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo -e "${RED}Killing existing process from $PID_FILE: $PID${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        rm "pids/$PID_FILE" 2>/dev/null || true
    fi
done

# Step 2: Start the enhanced WebSocket server
echo -e "${GREEN}Starting enhanced WebSocket server...${NC}"
python3 enhanced_ws_8765.py > logs/enhanced_ws_8765.out 2>&1 &

# Step 3: Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 3

# Step 4: Check if server started successfully
if [ -f pids/ws_server_8765.pid ]; then
    PID=$(cat pids/ws_server_8765.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}WebSocket server started successfully (PID: $PID)${NC}"
    else
        echo -e "${RED}WebSocket server process not running!${NC}"
        exit 1
    fi
else
    echo -e "${RED}WebSocket server PID file not found!${NC}"
    exit 1
fi

# Step 5: Run a quick test to verify it's working
echo -e "${BLUE}\nTesting connection to WebSocket server...${NC}"
python3 test_ws_memory.py
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}\nSystem is up and running with memory and advanced LLM integration!${NC}"
    echo -e "${YELLOW}Logs available at: logs/enhanced_ws_8765.log${NC}"
    echo -e "${BLUE}Use the following URLs:${NC}"
    echo -e "  - WebSocket: ws://localhost:8765"
    echo -e "${BLUE}Features enabled:${NC}"
    echo -e "  - Memory system with semantic search"
    echo -e "  - Advanced LLM (llava model)"
    echo -e "  - Context-aware responses based on screen content"
    echo -e "${YELLOW}To stop the server: bash stop_enhanced_system.sh${NC}"
else
    echo -e "${RED}\nTest failed - system might not be functioning correctly.${NC}"
    echo -e "${YELLOW}Check logs for details: logs/enhanced_ws_8765.log${NC}"
fi

exit 0