#\!/bin/bash

# Working System Startup Script
# Starts core components that are known to work

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"

echo -e "${GREEN}Starting SensAI Working System...${NC}"

# Create directories
mkdir -p "$LOG_DIR"/{websocket,backend,sensors,bridge}
mkdir -p "$PID_DIR"
mkdir -p "$SCRIPT_DIR/cache"

# Clean up
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "fixed_ws_8765" 2>/dev/null || true
pkill -f "enhanced_backend" 2>/dev/null || true
pkill -f "http.server" 2>/dev/null || true

# Kill processes on ports  
for port in 8765 8767 8080; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}Killing processes on port $port${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

sleep 2

# Start WebSocket server (fixed_ws_8765.py)
echo -e "${GREEN}Starting WebSocket server...${NC}"
if [ -f "$SCRIPT_DIR/fixed_ws_8765.py" ]; then
    nohup python3 "$SCRIPT_DIR/fixed_ws_8765.py" > "$LOG_DIR/websocket/ws_server.log" 2>&1 &
    ws_pid=$\!
    echo $ws_pid > "$PID_DIR/ws_server.pid"
    echo -e "${GREEN}WebSocket server started (PID: $ws_pid)${NC}"
    sleep 3
else
    echo -e "${RED}WebSocket server not found${NC}"
    exit 1
fi

# Start enhanced backend server  
echo -e "${GREEN}Starting backend server...${NC}"
if [ -f "$SCRIPT_DIR/enhanced_backend_server.py" ]; then
    nohup python3 "$SCRIPT_DIR/enhanced_backend_server.py" > "$LOG_DIR/backend/backend_server.log" 2>&1 &
    backend_pid=$\!
    echo $backend_pid > "$PID_DIR/backend_server.pid"
    echo -e "${GREEN}Backend server started (PID: $backend_pid)${NC}"
    sleep 3
else
    echo -e "${RED}Backend server not found${NC}"
    exit 1
fi

# Start overlay HTTP server for dashboard
echo -e "${GREEN}Starting overlay HTTP server...${NC}"
cd "$SCRIPT_DIR"
nohup python3 -m http.server 8080 > "$LOG_DIR/bridge/http_server.log" 2>&1 &
http_pid=$\!
echo $http_pid > "$PID_DIR/http_server.pid"
echo -e "${GREEN}HTTP server started on port 8080 (PID: $http_pid)${NC}"

sleep 2

# Test connectivity
echo -e "${GREEN}Testing connectivity...${NC}"
if lsof -ti :8765 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ WebSocket server responding on port 8765${NC}"
else
    echo -e "${RED}❌ WebSocket server not responding${NC}"
fi

if lsof -ti :8080 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ HTTP server responding on port 8080${NC}"
else
    echo -e "${RED}❌ HTTP server not responding${NC}"
fi

# Display status
echo
echo -e "${GREEN}=== SensAI Working System Started ===${NC}"
echo
echo -e "${GREEN}Running Components:${NC}"
echo -e "  ✅ WebSocket Server (PID: $ws_pid) - Port 8765"
echo -e "  ✅ Backend Server (PID: $backend_pid) - Port 8765"  
echo -e "  ✅ HTTP Server (PID: $http_pid) - Port 8080"

echo
echo -e "${GREEN}Access Points:${NC}"
echo -e "  🌐 System Dashboard: ${YELLOW}http://localhost:8080/system_dashboard.html${NC}"
echo -e "  💬 Chat Interface: ${YELLOW}http://localhost:8080/futuristic_overlay.html${NC}"
echo -e "  📊 Simple Chat: ${YELLOW}http://localhost:8080/templates/index.html${NC}"

echo
echo -e "${GREEN}Log Files:${NC}"
echo -e "  📄 WebSocket: $LOG_DIR/websocket/ws_server.log"
echo -e "  📄 Backend: $LOG_DIR/backend/backend_server.log"
echo -e "  📄 HTTP: $LOG_DIR/bridge/http_server.log"

echo
echo -e "${GREEN}Control:${NC}"
echo -e "  🛑 Stop System: ./stop_working_system.sh"
echo -e "  📊 Monitor: tail -f $LOG_DIR/websocket/ws_server.log"

echo
echo -e "${GREEN}🎉 Working system ready\!${NC}"
echo -e "${YELLOW}Open your browser to: http://localhost:8080/system_dashboard.html${NC}"
echo
echo -e "${GREEN}Press Ctrl+C to exit (system will keep running)${NC}"

# Keep script running briefly to show output
sleep 10
echo -e "${GREEN}System is running in background. Use stop_working_system.sh to stop.${NC}"
EOF < /dev/null