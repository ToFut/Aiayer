#!/bin/bash
# Minimal script to run WebSocket server with local LLM integration for Tauri overlay
# Inspired by start_optimized_system_with_llm.sh

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create required directories
mkdir -p logs pids cache/process_sensor cache/screen_sensor memory

echo -e "${BLUE}Starting Minimal Overlay System with LLM Integration...${NC}"

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
for PORT in 8765 8766 8767; do
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Killing processes on port $PORT: $PIDS${NC}"
        kill -9 $PIDS 2>/dev/null || true
    fi
done

# Kill any existing named processes
for PROCESS in "bridge_server" "ollama_service" "backend_server"; do
    if [ -f "pids/${PROCESS}.pid" ]; then
        PID=$(cat pids/${PROCESS}.pid)
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Killing ${PROCESS} process: $PID${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        rm pids/${PROCESS}.pid
    fi
done

# Start bridge server (for WebSocket communication)
echo -e "${GREEN}Starting bridge server for WebSocket communication...${NC}"
python3 ultra_simple_bridge.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo -e "${GREEN}Bridge server started with PID: $BRIDGE_PID${NC}"

# Wait for bridge to initialize
sleep 2

# Start Ollama LLM service
echo -e "${GREEN}Starting Ollama LLM service...${NC}"
python3 ollama_service_fixed.py > logs/ollama_service.log 2>&1 &
OLLAMA_PID=$!
echo $OLLAMA_PID > pids/ollama_service.pid
echo -e "${GREEN}Ollama LLM service started with PID: $OLLAMA_PID${NC}"

# Wait for Ollama to initialize
sleep 2

# Start enhanced backend server
echo -e "${GREEN}Starting enhanced backend server...${NC}"
python3 enhanced_backend_server.py > logs/backend_server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/backend_server.pid
echo -e "${GREEN}Enhanced backend server started with PID: $BACKEND_PID${NC}"

# Wait for everything to initialize
sleep 2

# Check if processes are running
echo -e "${BLUE}Checking if processes are running...${NC}"
FAILED=0

check_process() {
    if ! ps -p $1 > /dev/null; then
        echo -e "${RED}$2 is not running!${NC}"
        FAILED=1
    else
        echo -e "${GREEN}$2 is running (PID: $1)${NC}"
    fi
}

check_process $BRIDGE_PID "Bridge server"
check_process $OLLAMA_PID "Ollama LLM service"
check_process $BACKEND_PID "Enhanced backend server"

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}One or more processes failed to start. Check logs for details:${NC}"
    echo -e "${YELLOW}Bridge server: logs/bridge_server.log${NC}"
    echo -e "${YELLOW}Ollama service: logs/ollama_service.log${NC}"
    echo -e "${YELLOW}Backend server: logs/backend_server.log${NC}"
    exit 1
fi

echo -e "\n${GREEN}Minimal Overlay System is now running!${NC}"
echo -e "${BLUE}WebSocket server is running on: ws://localhost:8765${NC}"
echo -e "${BLUE}User messages will flow: Overlay → WebSocket → LLM → WebSocket → Overlay${NC}"

echo -e "\n${YELLOW}To monitor logs in real-time:${NC}"
echo -e "tail -f logs/bridge_server.log    # Bridge server logs"
echo -e "tail -f logs/ollama_service.log   # Ollama LLM service logs" 
echo -e "tail -f logs/backend_server.log   # Backend server logs"

echo -e "\n${YELLOW}To start the Tauri overlay:${NC}"
echo -e "cd overlay && npm run tauri dev"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "${RED}kill \$(cat pids/bridge_server.pid pids/ollama_service.pid pids/backend_server.pid)${NC}"