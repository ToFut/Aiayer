#!/bin/bash
# Script to stop the overlay interceptor service and reset the bridge URL

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stopping Overlay Interceptor Service${NC}"

# Kill existing interceptor if running
if [ -f "pids/response_interceptor.pid" ]; then
    PID=$(cat pids/response_interceptor.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Stopping interceptor service (PID: $PID)${NC}"
        kill $PID 2>/dev/null || true
        sleep 2
        if ps -p $PID > /dev/null; then
            echo -e "${RED}Service did not stop gracefully, forcing...${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}Interceptor service not running but PID file exists${NC}"
    fi
    rm -f pids/response_interceptor.pid
    echo -e "${GREEN}Interceptor service stopped${NC}"
else
    echo -e "${YELLOW}No interceptor service PID file found${NC}"
fi

# Reset the bridge URL
echo -e "${GREEN}Resetting overlay bridge URL to original (port 8765)${NC}"
python update_bridge_url.py --reset

echo -e "${GREEN}Overlay configuration has been reset${NC}"