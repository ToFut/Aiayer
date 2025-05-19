#!/bin/bash
# Minimal script to start only the WebSocket and LLM components for chat overlay
# Uses the same components as start_optimized_system_with_llm.sh but only the essential ones

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting minimal chat overlay with LocalLLM...${NC}"

# Create required directories
mkdir -p logs pids cache/process_sensor cache/screen_sensor cache/file_sensor memory

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
for PORT in 8765 8766 8767; do
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Killing processes on port $PORT: $PIDS${NC}"
        kill -9 $PIDS 2>/dev/null || true
    fi
done

# Kill existing processes if PID files exist
for SERVICE in "bridge_server" "ollama_service" "backend_server" "standalone_overlay_llm"; do
    if [ -f "pids/${SERVICE}.pid" ]; then
        PID=$(cat pids/${SERVICE}.pid)
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Killing ${SERVICE} process: $PID${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        rm pids/${SERVICE}.pid
    fi
done

# 1. Start the minimal bridge server for WebSocket communication
echo -e "${GREEN}Starting minimal bridge server for WebSocket communication...${NC}"
python3 minimal_bridge_server.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo -e "${GREEN}Bridge server started with PID: $BRIDGE_PID${NC}"

# Wait for bridge to initialize
sleep 2

# 2. Start Ollama LLM service to connect to local LLM
echo -e "${GREEN}Starting Ollama LLM service...${NC}"
python3 ollama_service_fixed.py > logs/ollama_service.log 2>&1 &
OLLAMA_PID=$!
echo $OLLAMA_PID > pids/ollama_service.pid
echo -e "${GREEN}Ollama LLM service started with PID: $OLLAMA_PID${NC}"

# Wait for LLM service to initialize
sleep 2

# 3. Start the enhanced backend server that handles context and LLM responses
echo -e "${GREEN}Starting enhanced backend server...${NC}"
python3 enhanced_backend_server.py > logs/backend_server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/backend_server.pid
echo -e "${GREEN}Enhanced backend server started with PID: $BACKEND_PID${NC}"

# Wait for all components to initialize
sleep 3

# Check if processes are running
echo -e "${BLUE}Checking if processes are running...${NC}"

check_process() {
    if ! ps -p $1 > /dev/null; then
        echo -e "${RED}$2 is not running!${NC}"
        echo -e "${YELLOW}Check log file: $3${NC}"
        # Attempt to show error from log
        echo -e "${YELLOW}Last 5 lines of log:${NC}"
        tail -n 5 $3
        return 1
    else
        echo -e "${GREEN}$2 is running (PID: $1)${NC}"
        return 0
    fi
}

FAILED=0
check_process $BRIDGE_PID "Bridge server" "logs/bridge_server.log" || FAILED=1
check_process $OLLAMA_PID "Ollama LLM service" "logs/ollama_service.log" || FAILED=1
check_process $BACKEND_PID "Enhanced backend server" "logs/backend_server.log" || FAILED=1

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}One or more processes failed to start.${NC}"
    echo -e "${RED}You may need to try running each component separately to troubleshoot.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Minimal chat overlay with LLM is now running!${NC}"
echo -e "${BLUE}WebSocket server is running on: ws://localhost:8765${NC}"
echo -e "${BLUE}LLM is integrated and ready to respond to user messages${NC}"

echo -e "\n${YELLOW}To start the Tauri overlay:${NC}"
echo -e "cd overlay && npm run tauri dev"

echo -e "\n${YELLOW}To monitor logs in real-time:${NC}"
echo -e "tail -f logs/bridge_server.log     # Bridge server logs"
echo -e "tail -f logs/ollama_service.log    # Ollama LLM service logs"
echo -e "tail -f logs/backend_server.log    # Backend server logs"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "${RED}kill \$(cat pids/bridge_server.pid pids/ollama_service.pid pids/backend_server.pid)${NC}"