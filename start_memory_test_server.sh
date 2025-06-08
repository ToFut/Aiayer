#!/bin/bash
# Start the Memory Test Server and open the web interface

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Starting Memory Test System${NC}"
echo -e "${BLUE}=======================================${NC}"

# Create log directories if they don't exist
mkdir -p logs/memory
mkdir -p pids
echo -e "${GREEN}Created log and pid directories${NC}"

# Check if the WebSocket server is already running
WS_PID=$(pgrep -f "python3 memory_test_server.py" || echo "")
if [ ! -z "$WS_PID" ]; then
    echo -e "${YELLOW}Memory Test Server is already running (PID: $WS_PID)${NC}"
    echo -e "${YELLOW}Stopping existing server...${NC}"
    kill $WS_PID
    sleep 2
fi

# Start the WebSocket server
echo -e "${GREEN}Starting Memory Test WebSocket Server...${NC}"
python3 memory_test_server.py > logs/memory_test_server.log 2>&1 &
WS_PID=$!

# Save PID for later shutdown
echo $WS_PID > pids/memory_test_ws_server.pid
echo -e "${GREEN}WebSocket Server started with PID: $WS_PID${NC}"

# Start a simple HTTP server to serve the web interface
echo -e "${GREEN}Starting HTTP Server for Web Interface...${NC}"

# Check if an HTTP server is already running
HTTP_PID=$(pgrep -f "python3 -m http.server 8081" || echo "")
if [ ! -z "$HTTP_PID" ]; then
    echo -e "${YELLOW}HTTP Server is already running (PID: $HTTP_PID)${NC}"
    echo -e "${YELLOW}Stopping existing server...${NC}"
    kill $HTTP_PID
    sleep 2
fi

# Start new HTTP server
cd "$(dirname "$0")" # Ensure we're in the script's directory
# Serve from the project root, not the memory_test subdirectory
python3 -m http.server 8081 > logs/memory_test_http.log 2>&1 &
HTTP_PID=$!

# Save PID for later shutdown
echo $HTTP_PID > pids/memory_test_http_server.pid
echo -e "${GREEN}HTTP Server started with PID: $HTTP_PID${NC}"

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to initialize...${NC}"
sleep 2

# Open the browser
echo -e "${GREEN}Opening Memory Test Interface in your browser...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8081/web/memory_test/
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:8081/web/memory_test/
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start http://localhost:8081/web/memory_test/
else
    echo -e "${YELLOW}Could not automatically open browser. Please open this URL manually:${NC}"
    echo -e "${BLUE}http://localhost:8081/web/memory_test/${NC}"
fi

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}Memory Test System is now running${NC}"
echo -e "${BLUE}WebSocket Server: ws://localhost:8769${NC}"
echo -e "${BLUE}Web Interface: http://localhost:8081/web/memory_test/${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "${YELLOW}To stop the servers, run: ./stop_memory_test_server.sh${NC}"