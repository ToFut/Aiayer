#!/bin/bash
# Script to start the enhanced backend server with WebSocket, Memory and LocalLLM integration

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Enhanced Backend Server with WebSocket, Memory and LocalLLM Integration...${NC}"

# Create required directories
mkdir -p logs pids

# Kill any existing backend server processes
echo -e "${YELLOW}Stopping any existing backend servers...${NC}"
if [ -f pids/backend_server.pid ]; then
    PID=$(cat pids/backend_server.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Killing backend server process: $PID${NC}"
        kill -9 $PID 2>/dev/null || true
    fi
    rm pids/backend_server.pid
fi

# Also kill any WebSocket processes on port 8765
echo -e "${YELLOW}Checking for any processes on port 8765...${NC}"
PORT_PIDS=$(lsof -ti :8765 2>/dev/null)
if [ -n "$PORT_PIDS" ]; then
    echo -e "${YELLOW}Killing processes on port 8765: $PORT_PIDS${NC}"
    kill -9 $PORT_PIDS 2>/dev/null || true
fi

# Additional kill for any Python processes running WebSocket servers
pkill -f "enhanced_backend_server.py" 2>/dev/null || true
pkill -f "enhanced_ws_8765.py" 2>/dev/null || true
sleep 1

# Make the script executable
chmod +x enhanced_backend_server.py

# Start the enhanced backend server
echo -e "${GREEN}Starting enhanced backend server...${NC}"
python3 enhanced_backend_server.py > logs/enhanced_backend.out 2>&1 &
BACKEND_PID=$!

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 3

# Check if server is still running
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}Backend server started successfully. PID: $BACKEND_PID${NC}"
    # Save PID to file (already done in the script, but as a backup)
    echo $BACKEND_PID > pids/backend_server.pid
else
    echo -e "${RED}Backend server failed to start.${NC}"
    exit 1
fi

# Print success message
echo -e "${GREEN}Backend server is now running with WebSocket, Memory and LocalLLM integration${NC}"
echo -e "${BLUE}WebSocket URL: ws://localhost:8765${NC}"
echo -e "${YELLOW}To monitor logs: tail -f logs/backend_server.log${NC}"
echo -e "${YELLOW}To stop the server: kill $BACKEND_PID${NC}"

echo -e "\n${GREEN}Backend is ready to handle requests from frontend applications${NC}"
echo -e "${BLUE}User messages will flow: Frontend → Backend → LocalLLM → Backend → Frontend${NC}"