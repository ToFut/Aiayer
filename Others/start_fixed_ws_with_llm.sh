#!/bin/bash
# Script to start the enhanced WebSocket server with memory and LocalLLM integration

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting WebSocket Server with Memory and LocalLLM Integration...${NC}"

# Create required directories
mkdir -p logs pids

# Kill any existing WebSocket server processes
echo -e "${YELLOW}Stopping any existing WebSocket servers...${NC}"
if [ -f pids/ws_server_8765.pid ]; then
    PID=$(cat pids/ws_server_8765.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Killing WebSocket server process: $PID${NC}"
        kill -9 $PID 2>/dev/null || true
    fi
    rm pids/ws_server_8765.pid
fi

# Additional kill for any Python processes running WebSocket servers
pkill -f "fixed_ws_8765.py" 2>/dev/null || true
pkill -f "enhanced_ws_8765.py" 2>/dev/null || true
pkill -f "ws_server_8765" 2>/dev/null || true
sleep 1

# Start the enhanced WebSocket server with memory and LocalLLM
echo -e "${GREEN}Starting WebSocket server with memory and LocalLLM integration...${NC}"
python3 fixed_ws_8765.py > logs/fixed_ws_8765.out 2>&1 &

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 3

# Check if server started successfully
if [ -f pids/ws_server_8765.pid ]; then
    PID=$(cat pids/ws_server_8765.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}WebSocket server started successfully. PID: $PID${NC}"
    else
        echo -e "${RED}WebSocket server failed to start.${NC}"
        exit 1
    fi
else
    echo -e "${RED}WebSocket server PID file not found.${NC}"
    exit 1
fi

# Print success message
echo -e "${GREEN}WebSocket server with memory and LocalLLM integration is now running${NC}"
echo -e "${BLUE}WebSocket URL: ws://localhost:8765${NC}"
echo -e "${YELLOW}To monitor logs: tail -f logs/fixed_ws_8765.log${NC}"
echo -e "${YELLOW}To stop the server: kill $PID${NC}"