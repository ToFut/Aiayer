#!/bin/bash
# Stop Neural UI Detector Server

# Colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}       Stopping Neural UI Detector Server                    ${NC}"
echo -e "${BLUE}=============================================================${NC}"

# Check for saved PID file
if [ -f "logs/neural_ui_detector/server.pid" ]; then
    PID=$(cat logs/neural_ui_detector/server.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Stopping Neural UI Detector Server with PID: $PID${NC}"
        kill -9 $PID
        echo -e "${GREEN}Server stopped successfully${NC}"
    else
        echo -e "${YELLOW}No running server found with saved PID: $PID${NC}"
    fi
    # Clean up PID file
    rm logs/neural_ui_detector/server.pid
fi

# Check for any processes on port 8768
PID=$(lsof -ti:8768)
if [ -n "$PID" ]; then
    echo -e "${YELLOW}Found process on port 8768 (PID: $PID), stopping...${NC}"
    kill -9 $PID
    echo -e "${GREEN}Process stopped successfully${NC}"
fi

# Also check port 8769 (alternative port)
PID=$(lsof -ti:8769)
if [ -n "$PID" ]; then
    echo -e "${YELLOW}Found process on port 8769 (PID: $PID), stopping...${NC}"
    kill -9 $PID
    echo -e "${GREEN}Process stopped successfully${NC}"
fi

echo -e "${BLUE}=============================================================${NC}"
echo -e "${GREEN}Neural UI Detector Server stopped${NC}"
echo -e "${BLUE}=============================================================${NC}"