#!/bin/bash
# Start Neural UI Detector Server

# Colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}       Starting Neural UI Detector Server (Port 8768)        ${NC}"
echo -e "${BLUE}=============================================================${NC}"

# Create log directory if it doesn't exist
mkdir -p logs/neural_ui_detector

# Check if the server is already running
PID=$(lsof -ti:8768)
if [ -n "$PID" ]; then
    echo -e "${YELLOW}Neural UI Detector Server is already running on port 8768 (PID: $PID)${NC}"
    echo -e "${YELLOW}Stopping existing server...${NC}"
    kill -9 $PID
    sleep 1
fi

# Install required dependencies if missing
echo -e "${BLUE}Checking for required dependencies...${NC}"
python3 -m pip install --quiet websockets opencv-python pillow numpy

# Start the server
echo -e "${GREEN}Starting Neural UI Detector Server...${NC}"
python3 neural_ui_detector_server.py --port 8768 > logs/neural_ui_detector/startup.log 2>&1 &
SERVER_PID=$!

# Save PID for later use
echo $SERVER_PID > logs/neural_ui_detector/server.pid

# Wait a moment for the server to start
sleep 2

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}Neural UI Detector Server started successfully!${NC}"
    echo -e "${GREEN}PID: $SERVER_PID${NC}"
    
    # Find the actual port being used
    PORT=$(cat neural_ui_detector_port.txt 2>/dev/null || echo "8768")
    echo -e "${GREEN}Server running on WebSocket port: $PORT${NC}"
    
    # Provide instructions for testing
    echo -e "${BLUE}=============================================================${NC}"
    echo -e "${YELLOW}To test the Neural UI Detector:${NC}"
    echo -e "  1. Open in your browser: ${BLUE}test_neural_ui_detector_fixed.html${NC}"
    echo -e "  2. Or connect to WebSocket: ${BLUE}ws://localhost:$PORT${NC}"
    echo -e "${BLUE}=============================================================${NC}"
else
    echo -e "${RED}Failed to start Neural UI Detector Server${NC}"
    echo -e "${YELLOW}Check logs at: logs/neural_ui_detector/startup.log${NC}"
fi