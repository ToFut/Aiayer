#!/bin/bash
# Enhanced startup script for Local Assistant with bridge fixes
# This script improves on start_fixed.sh by adding better diagnostics, 
# system state checking, and bridge recovery mechanisms

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  Starting Local Assistant System (Enhanced Version)${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""

# Functions for better script organization
function check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

function kill_port() {
    local port=$1
    if check_port $port; then
        echo -e "${YELLOW}Killing process on port $port...${NC}"
        lsof -ti :$port | xargs kill -9
        sleep 1
    fi
}

function check_pid_running() {
    local pid=$1
    if ps -p "$pid" > /dev/null; then
        return 0 # Process is running
    else
        return 1 # Process is not running
    fi
}

function wait_for_port() {
    local port=$1
    local timeout=$2
    local count=0
    
    echo -n "Waiting for port $port to be available"
    while check_port "$port" && [ $count -lt "$timeout" ]; do
        echo -n "."
        sleep 1
        count=$((count+1))
    done
    
    if [ $count -lt "$timeout" ]; then
        echo -e " ${GREEN}OK${NC}"
        return 0
    else
        echo -e " ${RED}TIMEOUT${NC}"
        return 1
    fi
}

# First, ensure we have clean state by stopping all processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
# Kill any existing processes
for port in 8765 8766 5001 5002 11434 1420 1430; do
    kill_port "$port"
done

# Kill specific processes
pkill -9 -f "websocket_server.py|main_with_overlay.py|main.py" 2>/dev/null || true

# Wait to ensure ports are released
sleep 2

# Create logs directory with proper permissions
echo "Creating logs directory..."
mkdir -p logs
chmod 755 logs

# Clear old log files for a clean start
echo "Clearing old log files..."
find logs -name "*.log" -type f -exec truncate -s 0 {} \;

# Check Ollama status and restart if needed
echo -e "${YELLOW}Checking Ollama LLM service...${NC}"
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo -e "  Ollama is ${GREEN}already running${NC}"
    OLLAMA_RUNNING=true
else
    echo "  Ollama is not running, attempting to start"
    if command -v ollama >/dev/null 2>&1; then
        ollama serve > logs/ollama.log 2>&1 &
        OLLAMA_PID=$!
        echo "  Started Ollama (PID: $OLLAMA_PID)"
        
        # Wait for Ollama to start
        echo -n "  Waiting for Ollama to initialize"
        for i in {1..15}; do
            if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
                echo -e " ${GREEN}OK${NC}"
                OLLAMA_RUNNING=true
                break
            fi
            echo -n "."
            sleep 1
        done
        
        if [ -z "$OLLAMA_RUNNING" ]; then
            echo -e " ${RED}FAILED${NC}"
            echo "  Ollama failed to start, but continuing with fallback mode"
        fi
    else
        echo "  Ollama not found. The system will use fallback LLM."
    fi
fi

# Set environment variables for better configuration
export PYTHONUNBUFFERED=1
export DEBUG_MODE=1
export LOG_LEVEL=INFO

# Start WebSocket server with port selection
echo -e "${YELLOW}Starting WebSocket server...${NC}"
WEBSOCKET_PORT=8765

if check_port "$WEBSOCKET_PORT"; then
    echo "  Port $WEBSOCKET_PORT is already in use, clearing it"
    kill_port "$WEBSOCKET_PORT"
    wait_for_port "$WEBSOCKET_PORT" 5
fi

# Start WebSocket server with explicit arguments for better debugging
python websocket_server.py --port "$WEBSOCKET_PORT" --debug > logs/websocket.log 2>&1 &
WEBSOCKET_PID=$!
echo "  WebSocket server started on port $WEBSOCKET_PORT (PID: $WEBSOCKET_PID)"

# Wait for WebSocket server to start and verify it's running
echo -n "  Waiting for WebSocket server to initialize"
for i in {1..10}; do
    if check_pid_running "$WEBSOCKET_PID"; then
        # Try to connect to the WebSocket server
        if curl -s --include \
            --no-buffer \
            --header "Connection: Upgrade" \
            --header "Upgrade: websocket" \
            --header "Host: localhost:$WEBSOCKET_PORT" \
            --header "Origin: http://localhost:$WEBSOCKET_PORT" \
            --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
            --header "Sec-WebSocket-Version: 13" \
            http://localhost:$WEBSOCKET_PORT/ \
            2>/dev/null | grep -q "Switching Protocols"; then
            echo -e " ${GREEN}OK${NC}"
            WEBSOCKET_RUNNING=true
            break
        fi
    else
        # WebSocket server died
        echo -e " ${RED}FAILED - Process died${NC}"
        # Check the log for clues
        tail -n 5 logs/websocket.log
        break
    fi
    echo -n "."
    sleep 1
done

if [ -z "$WEBSOCKET_RUNNING" ]; then
    echo -e " ${RED}FAILED${NC}"
    echo "  WebSocket server failed to start properly."
    echo "  Trying to restart on alternative port..."
    
    WEBSOCKET_PORT=8766
    python websocket_server.py --port "$WEBSOCKET_PORT" --debug > logs/websocket.log 2>&1 &
    WEBSOCKET_PID=$!
    echo "  WebSocket server started on alternative port $WEBSOCKET_PORT (PID: $WEBSOCKET_PID)"
    sleep 3
fi

# Always export the WebSocket port for other components
export WEBSOCKET_PORT="$WEBSOCKET_PORT"

# Start main application with overlay support
echo -e "${YELLOW}Starting main application...${NC}"
FLASK_PORT=5002

if check_port "$FLASK_PORT"; then
    echo "  Port $FLASK_PORT is already in use, clearing it"
    kill_port "$FLASK_PORT"
    wait_for_port "$FLASK_PORT" 5
fi

# Set environment variables for Flask
export FLASK_APP=main_with_overlay.py
export FLASK_ENV=development
export FLASK_RUN_PORT="$FLASK_PORT"

# Start main application with explicit configuration
LOG_LEVEL=INFO python main_with_overlay.py > logs/main_app.log 2>&1 &
MAIN_PID=$!
echo "  Main application started (PID: $MAIN_PID)"

# Wait for main app to initialize
echo -n "  Waiting for main application to initialize"
for i in {1..10}; do
    if check_pid_running "$MAIN_PID"; then
        # The process is still running
        if curl -s http://localhost:"$FLASK_PORT"/health 2>/dev/null | grep -q "OK"; then
            echo -e " ${GREEN}OK${NC}"
            MAIN_RUNNING=true
            break
        fi
    else
        # Main app died
        echo -e " ${RED}FAILED - Process died${NC}"
        # Check the log for clues
        tail -n 10 logs/main_app.log
        break
    fi
    echo -n "."
    sleep 1
done

if [ -z "$MAIN_RUNNING" ]; then
    echo -e " ${RED}FAILED${NC}"
    echo "  Main application failed to start properly."
    # Try to restart with fallback options
    LOG_LEVEL=DEBUG python main_with_overlay.py --fallback-mode > logs/main_app.log 2>&1 &
    MAIN_PID=$!
    echo "  Started main application in fallback mode (PID: $MAIN_PID)"
    sleep 5
fi

# Run test_bridge.py to verify system communication
echo -e "${YELLOW}Testing bridge communication...${NC}"
python test_bridge.py > logs/test_bridge.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "  Bridge test ${GREEN}PASSED${NC}"
    BRIDGE_OK=true
else
    echo -e "  Bridge test ${RED}FAILED${NC}"
    echo "  See logs/test_bridge.log for details"
    
    # Attempt to fix bridge issues
    echo "  Attempting to fix bridge issues..."
    python direct_ui_fix.py > /dev/null 2>&1
    python force_completion.py > /dev/null 2>&1
    python emergency_clear.py > /dev/null 2>&1
    
    # Run the test again to see if it's fixed
    python test_bridge.py > logs/test_bridge_retry.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "  Bridge test retry ${GREEN}PASSED${NC}"
        BRIDGE_OK=true
    else
        echo -e "  Bridge test retry ${RED}FAILED${NC}"
    fi
fi

# Start overlay UI with modified port
echo -e "${YELLOW}Starting overlay UI...${NC}"
cd overlay || exit

# Check if node_modules exists, if not, try to use the backup or run npm install
if [ ! -d "node_modules" ]; then
    if [ -d "../overlay_node_modules_backup/node_modules" ]; then
        echo "  Restoring node_modules from backup..."
        mv ../overlay_node_modules_backup/node_modules .
    else
        echo "  Installing dependencies for overlay..."
        npm install
    fi
fi

# Try to start the overlay
echo "  Attempting to start overlay..."
npm run tauri dev > ../logs/overlay.log 2>&1 &
OVERLAY_PID=$!
cd ..

# Give the overlay a few seconds to start up
echo -n "  Waiting for overlay UI to initialize"
for i in {1..10}; do
    if check_pid_running "$OVERLAY_PID"; then
        echo -n "."
    else
        # Process died
        echo -e " ${RED}FAILED${NC}"
        break
    fi
    sleep 1
done
echo -e " ${GREEN}OK${NC}"

# Run UI fix to ensure no stuck messages
echo -e "${YELLOW}Running UI fix scripts...${NC}"
python ui_fix.py > logs/ui_fix.log 2>&1
python direct_ui_fix.py > logs/direct_ui_fix.log 2>&1
python force_completion.py > logs/force_completion.log 2>&1
echo -e "  UI fixes ${GREEN}completed${NC}"

# ENHANCED: Create a bridge watchdog that monitors and fixes bridge issues
echo -e "${YELLOW}Starting bridge watchdog...${NC}"
(
    while true; do
        # Check if processes are still running
        RESTART_NEEDED=false
        
        if ! check_pid_running "$WEBSOCKET_PID"; then
            echo "[$(date)] WebSocket server died, restarting..." >> logs/watchdog.log
            python websocket_server.py --port "$WEBSOCKET_PORT" --debug > logs/websocket.log 2>&1 &
            WEBSOCKET_PID=$!
            RESTART_NEEDED=true
        fi
        
        if ! check_pid_running "$MAIN_PID"; then
            echo "[$(date)] Main application died, restarting..." >> logs/watchdog.log
            LOG_LEVEL=INFO python main_with_overlay.py > logs/main_app.log 2>&1 &
            MAIN_PID=$!
            RESTART_NEEDED=true
        fi
        
        # If we had to restart something, run the UI fixes
        if [ "$RESTART_NEEDED" = true ]; then
            sleep 5
            echo "[$(date)] Running UI fixes after restart..." >> logs/watchdog.log
            python ui_fix.py > /dev/null 2>&1
            python direct_ui_fix.py > /dev/null 2>&1
            python force_completion.py > /dev/null 2>&1
        fi
        
        # Every 5 minutes, run a UI fix just to be safe
        if [ $((RANDOM % 30)) -eq 0 ]; then
            echo "[$(date)] Running periodic UI fix..." >> logs/watchdog.log
            python direct_ui_fix.py > /dev/null 2>&1
        fi
        
        sleep 30
    done
) > logs/watchdog.log 2>&1 &
WATCHDOG_PID=$!
echo "  Bridge watchdog started (PID: $WATCHDOG_PID)"

echo
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  All components started!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo
echo -e "${BLUE}Running services:${NC}"
echo "- WebSocket server: ws://localhost:$WEBSOCKET_PORT (PID: $WEBSOCKET_PID)"
echo "- Main application: http://localhost:$FLASK_PORT (PID: $MAIN_PID)"
echo "- Overlay UI (PID: $OVERLAY_PID)"
echo "- Bridge Watchdog (PID: $WATCHDOG_PID)"
if [ -n "$OLLAMA_RUNNING" ]; then
    echo "- Ollama LLM: http://localhost:11434"
fi

if [ -n "$BRIDGE_OK" ]; then
    echo -e "${GREEN}Bridge communication verified and working${NC}"
else
    echo -e "${YELLOW}Bridge communication not verified - check logs${NC}"
fi

echo
echo -e "${BLUE}View logs:${NC}"
echo "- WebSocket: tail -f logs/websocket.log"
echo "- Main app: tail -f logs/main_app.log"
echo "- Overlay: tail -f logs/overlay.log"
echo "- Bridge: tail -f logs/test_bridge.log"
echo "- Watchdog: tail -f logs/watchdog.log"
echo
echo "To stop all services, press Ctrl+C in this terminal"
echo "or run './stop.sh' from another terminal."
echo

# Define trap to clean up on exit
trap 'echo "Stopping all services..."; kill $WEBSOCKET_PID $MAIN_PID $OVERLAY_PID $WATCHDOG_PID 2>/dev/null; pkill -f "ollama" 2>/dev/null || true' INT TERM EXIT

# Keep the script running with a robust health check
echo "System is running. Press Ctrl+C to stop all components..."
while true; do
    # Check if critical components are still running
    RESTART_NEEDED=false
    
    if ! check_pid_running "$WEBSOCKET_PID"; then
        echo -e "${RED}WebSocket server died, restarting...${NC}"
        python websocket_server.py --port "$WEBSOCKET_PORT" --debug > logs/websocket.log 2>&1 &
        WEBSOCKET_PID=$!
        RESTART_NEEDED=true
    fi
    
    if ! check_pid_running "$MAIN_PID"; then
        echo -e "${RED}Main application died, restarting...${NC}"
        LOG_LEVEL=INFO python main_with_overlay.py > logs/main_app.log 2>&1 &
        MAIN_PID=$!
        RESTART_NEEDED=true
    fi
    
    if [ "$RESTART_NEEDED" = true ]; then
        echo "Running UI fixes after component restart..."
        sleep 5
        python ui_fix.py > /dev/null 2>&1
        python direct_ui_fix.py > /dev/null 2>&1
        python force_completion.py > /dev/null 2>&1
    fi
    
    sleep 30
done