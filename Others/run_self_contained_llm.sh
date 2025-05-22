#!/bin/bash
# Simple script to run the self-contained WebSocket LLM server

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Self-contained WebSocket LLM Server...${NC}"

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes on WebSocket port...${NC}"
PIDS=$(lsof -ti:8765 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Killing processes on port 8765: $PIDS${NC}"
    kill -9 $PIDS 2>/dev/null || true
fi

# Stop existing process if PID file exists
if [ -f "pids/self_contained_llm_ws.pid" ]; then
    PID=$(cat pids/self_contained_llm_ws.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Killing existing process: $PID${NC}"
        kill -9 $PID 2>/dev/null || true
    fi
    rm pids/self_contained_llm_ws.pid
fi

# Make script executable
chmod +x self_contained_llm_ws.py

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the self-contained server
echo -e "${GREEN}Starting self-contained LLM WebSocket server...${NC}"
python3 self_contained_llm_ws.py > logs/self_contained_llm_ws.log 2>&1 &
SERVER_PID=$!

# Wait for server to initialize
sleep 2

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}Server is running successfully with PID: $SERVER_PID${NC}"
else
    echo -e "${RED}Server failed to start! Check logs for details: logs/self_contained_llm_ws.log${NC}"
    tail -n 10 logs/self_contained_llm_ws.log
    exit 1
fi

echo -e "\n${GREEN}Self-contained WebSocket LLM server is now running!${NC}"
echo -e "${BLUE}WebSocket server is running on: ws://localhost:8765${NC}"
echo -e "${BLUE}This single server handles both the WebSocket connections and LLM integration${NC}"

echo -e "\n${YELLOW}To monitor logs in real-time:${NC}"
echo -e "tail -f logs/self_contained_llm_ws.log"

echo -e "\n${YELLOW}To start the Tauri overlay:${NC}"
echo -e "cd overlay && npm run tauri dev"

echo -e "\n${YELLOW}To stop the server:${NC}"
echo -e "${RED}kill $SERVER_PID${NC}"