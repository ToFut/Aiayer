#!/bin/bash
# Script to start the overlay with interceptor service
# This ensures reliable LLM responses with ollama3.2:latest and 30-second timeout

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Overlay with Interceptor Service${NC}"
echo "This will use ollama3.2:latest with a 30-second timeout"

# Check if Ollama is running
if ! curl -s "http://localhost:11434/api/version" > /dev/null; then
    echo -e "${RED}Error: Ollama is not running. Please start Ollama first.${NC}"
    echo "You can start Ollama with: ollama serve"
    exit 1
fi

# Check if the WebSocket server is already running
if curl -s "http://localhost:8765" > /dev/null 2>&1; then
    echo -e "${YELLOW}WebSocket server detected at port 8765${NC}"
else
    echo -e "${YELLOW}No WebSocket server detected at port 8765. Make sure to start it.${NC}"
    echo "You can start the server with: python enhanced_backend_server.py"
fi

# Create logs and pids directories if they don't exist
mkdir -p logs pids

# Kill existing interceptor if running
if [ -f "pids/response_interceptor.pid" ]; then
    PID=$(cat pids/response_interceptor.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Stopping existing interceptor service (PID: $PID)${NC}"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
    rm -f pids/response_interceptor.pid
fi

# Update the bridge URL to use the interceptor
echo -e "${GREEN}Updating overlay bridge to use the interceptor${NC}"
python update_bridge_url.py --port 8766

# Start the interceptor service
echo -e "${GREEN}Starting interceptor service...${NC}"
python overlay_response_interceptor.py > logs/interceptor_output.log 2>&1 &

# Wait a moment to ensure it's started
sleep 2

# Check if the interceptor is running
if [ -f "pids/response_interceptor.pid" ]; then
    INTERCEPTOR_PID=$(cat pids/response_interceptor.pid)
    if ps -p $INTERCEPTOR_PID > /dev/null; then
        echo -e "${GREEN}Interceptor service is running (PID: $INTERCEPTOR_PID)${NC}"
    else
        echo -e "${RED}Failed to start interceptor service${NC}"
        exit 1
    fi
else
    echo -e "${RED}Failed to start interceptor service - no PID file found${NC}"
    exit 1
fi

echo -e "${GREEN}Overlay is now set up to use the interceptor service${NC}"
echo "You can now start the overlay with your usual command"
echo ""
echo -e "${YELLOW}To reset overlay bridge URL to original:${NC}"
echo "python update_bridge_url.py --reset"
echo ""
echo -e "${YELLOW}To stop the interceptor:${NC}"
echo "kill \$(cat pids/response_interceptor.pid)"