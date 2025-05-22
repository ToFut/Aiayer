#!/bin/bash

# Enhanced Next Generation AI Assistant Overlay with Agent Automation
# This script starts the complete system with automation capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"
MEMORY_DIR="$SCRIPT_DIR/memory"
HTTP_PORT=8080
BRIDGE_FRONTEND_PORT=8765
BRIDGE_BACKEND_PORT=8766

# Create required directories
mkdir -p "$LOG_DIR" "$PID_DIR" "$MEMORY_DIR"

echo -e "${PURPLE}================================================================${NC}"
echo -e "${PURPLE}    🤖 Enhanced Next Gen AI Assistant with Automation${NC}"
echo -e "${PURPLE}================================================================${NC}"
echo ""
echo -e "${CYAN}Features:${NC}"
echo -e "  💬 Natural language chat interface"
echo -e "  🎯 Smart automation suggestions"
echo -e "  ⌨️  Keyboard and mouse control"
echo -e "  🚨 Emergency shutdown (Ctrl+1)"
echo -e "  🛡️  Safety confirmations for actions"
echo -e "  💾 Memory and context integration"
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process by PID file
kill_by_pidfile() {
    local pidfile=$1
    if [[ -f "$pidfile" ]]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping existing process (PID: $pid)...${NC}"
            kill "$pid" 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$pidfile"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down Enhanced Next Gen Overlay...${NC}"
    
    # Stop all our processes
    kill_by_pidfile "$PID_DIR/advanced_bridge.pid"
    kill_by_pidfile "$PID_DIR/http_server.pid"
    
    # Kill any remaining processes on our ports
    for port in $HTTP_PORT $BRIDGE_FRONTEND_PORT $BRIDGE_BACKEND_PORT; do
        if check_port $port; then
            echo -e "${YELLOW}Killing process on port $port...${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ Shutdown complete${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Check for required files
required_files=(
    "futuristic_overlay.html"
    "advanced_bridge.py"
    "agent_workflow/input_controller.py"
    "agent_workflow/context_aware_agent.py"
)

echo -e "${BLUE}🔍 Checking required files...${NC}"
for file in "${required_files[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        echo -e "${RED}❌ Required file not found: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All required files found${NC}"

# Check for Python dependencies
echo -e "${BLUE}🔍 Checking Python dependencies...${NC}"
python3 -c "
import sys
try:
    import websockets
    import pyautogui
    import pynput
    print('✅ All Python dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    print('Please install with: pip install websockets pyautogui pynput')
    sys.exit(1)
" || exit 1

# Stop any existing processes
echo -e "${BLUE}🛑 Stopping any existing processes...${NC}"
kill_by_pidfile "$PID_DIR/advanced_bridge.pid"
kill_by_pidfile "$PID_DIR/http_server.pid"

# Check ports
echo -e "${BLUE}🔍 Checking ports...${NC}"
for port in $HTTP_PORT $BRIDGE_FRONTEND_PORT $BRIDGE_BACKEND_PORT; do
    if check_port $port; then
        echo -e "${YELLOW}⚠️  Port $port is in use, attempting to free it...${NC}"
        lsof -ti:$port | xargs kill 2>/dev/null || true
        sleep 2
        if check_port $port; then
            echo -e "${RED}❌ Could not free port $port${NC}"
            exit 1
        fi
    fi
done
echo -e "${GREEN}✅ All ports available${NC}"

# Start the Enhanced Advanced Bridge Server
echo -e "${BLUE}🚀 Starting Enhanced Advanced Bridge Server...${NC}"
python3 "$SCRIPT_DIR/advanced_bridge.py" \
    > "$LOG_DIR/bridge_output.log" 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > "$PID_DIR/advanced_bridge.pid"

# Wait for bridge to start
echo -e "${YELLOW}⏳ Waiting for bridge server to start...${NC}"
sleep 3

# Check if bridge is running
if ! kill -0 $BRIDGE_PID 2>/dev/null; then
    echo -e "${RED}❌ Bridge server failed to start. Check logs:${NC}"
    cat "$LOG_DIR/bridge_output.log"
    exit 1
fi

# Verify bridge ports are listening
for port in $BRIDGE_FRONTEND_PORT $BRIDGE_BACKEND_PORT; do
    if ! check_port $port; then
        echo -e "${RED}❌ Bridge server not listening on port $port${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Enhanced Advanced Bridge Server started (PID: $BRIDGE_PID)${NC}"

# Start HTTP server for the overlay
echo -e "${BLUE}🌐 Starting HTTP server on port $HTTP_PORT...${NC}"
python3 -m http.server $HTTP_PORT \
    > "$LOG_DIR/http_server.log" 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > "$PID_DIR/http_server.pid"

# Wait for HTTP server to start
sleep 2

# Check if HTTP server is running
if ! kill -0 $HTTP_PID 2>/dev/null; then
    echo -e "${RED}❌ HTTP server failed to start${NC}"
    exit 1
fi

if ! check_port $HTTP_PORT; then
    echo -e "${RED}❌ HTTP server not listening on port $HTTP_PORT${NC}"
    exit 1
fi

echo -e "${GREEN}✅ HTTP server started (PID: $HTTP_PID)${NC}"

# Display connection information
echo ""
echo -e "${PURPLE}================================================================${NC}"
echo -e "${GREEN}🎉 Enhanced Next Gen Overlay with Automation is running!${NC}"
echo -e "${PURPLE}================================================================${NC}"
echo ""
echo -e "${CYAN}📱 Overlay URL:${NC} http://localhost:$HTTP_PORT/futuristic_overlay.html"
echo -e "${CYAN}🔗 Bridge Frontend:${NC} ws://localhost:$BRIDGE_FRONTEND_PORT"
echo -e "${CYAN}🔗 Bridge Backend:${NC} ws://localhost:$BRIDGE_BACKEND_PORT"
echo ""
echo -e "${CYAN}📁 Log files:${NC}"
echo -e "  • Bridge: $LOG_DIR/bridge_output.log"
echo -e "  • HTTP: $LOG_DIR/http_server.log"
echo ""
echo -e "${YELLOW}🚨 SAFETY FEATURES:${NC}"
echo -e "  • Press ${RED}Ctrl+1${NC} for emergency stop"
echo -e "  • All automation requires user confirmation"
echo -e "  • Emergency button in chat interface"
echo ""
echo -e "${GREEN}💡 Usage:${NC}"
echo -e "  1. Click the eye icon (👁️) to open chat"
echo -e "  2. Ask for help with automation tasks"
echo -e "  3. Approve or reject automation suggestions"
echo -e "  4. Use emergency stop if needed"
echo ""

# Attempt to open in browser (macOS)
if command -v open >/dev/null 2>&1; then
    echo -e "${BLUE}🌐 Opening overlay in default browser...${NC}"
    open "http://localhost:$HTTP_PORT/futuristic_overlay.html" 2>/dev/null || true
elif command -v xdg-open >/dev/null 2>&1; then
    echo -e "${BLUE}🌐 Opening overlay in default browser...${NC}"
    xdg-open "http://localhost:$HTTP_PORT/futuristic_overlay.html" 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  Could not auto-open browser. Please visit:${NC}"
    echo -e "${CYAN}http://localhost:$HTTP_PORT/futuristic_overlay.html${NC}"
fi

echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Monitor processes
while true; do
    # Check if bridge is still running
    if ! kill -0 $BRIDGE_PID 2>/dev/null; then
        echo -e "${RED}❌ Bridge server stopped unexpectedly${NC}"
        break
    fi
    
    # Check if HTTP server is still running
    if ! kill -0 $HTTP_PID 2>/dev/null; then
        echo -e "${RED}❌ HTTP server stopped unexpectedly${NC}"
        break
    fi
    
    sleep 5
done

exit 0