#!/bin/bash
# Simple script to run the standalone overlay LLM system

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Standalone Overlay LLM System...${NC}"

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
for PORT in 8765; do
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Killing processes on port $PORT: $PIDS${NC}"
        kill -9 $PIDS 2>/dev/null || true
    fi
done

# Kill existing process if PID file exists
if [ -f "pids/standalone_overlay_llm.pid" ]; then
    PID=$(cat pids/standalone_overlay_llm.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Killing existing process: $PID${NC}"
        kill -9 $PID 2>/dev/null || true
    fi
    rm pids/standalone_overlay_llm.pid
fi

# Make script executable
chmod +x standalone_overlay_llm.py

# Start the standalone server
echo -e "${GREEN}Starting standalone overlay LLM server...${NC}"
python3 standalone_overlay_llm.py > logs/standalone_overlay_llm.log 2>&1 &
SERVER_PID=$!

# Wait for server to initialize
sleep 2

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}Standalone server is running successfully with PID: $SERVER_PID${NC}"
else
    echo -e "${RED}Server failed to start! Check logs for details: logs/standalone_overlay_llm.log${NC}"
    exit 1
fi

echo -e "\n${GREEN}Standalone Overlay LLM is now running!${NC}"
echo -e "${BLUE}WebSocket server is running on: ws://localhost:8765${NC}"
echo -e "${BLUE}User messages will flow: Overlay → WebSocket → LLM → WebSocket → Overlay${NC}"

echo -e "\n${YELLOW}To monitor logs in real-time:${NC}"
echo -e "tail -f logs/standalone_overlay_llm.log"

echo -e "\n${YELLOW}To start the Tauri overlay:${NC}"
echo -e "cd overlay && npm run tauri dev"

echo -e "\n${YELLOW}To stop the server:${NC}"
echo -e "${RED}kill $SERVER_PID${NC}"