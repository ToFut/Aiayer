#!/bin/bash

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Neural UI Detector Test Environment ====${NC}"

# Check if the neural_ui_detector_server.py file exists
if [ ! -f "neural_ui_detector_server.py" ]; then
    echo -e "${RED}Error: neural_ui_detector_server.py not found in the current directory.${NC}"
    exit 1
fi

# Check if test HTML file exists
if [ ! -f "test_neural_ui_detector_fixed.html" ]; then
    echo -e "${RED}Error: test_neural_ui_detector_fixed.html not found.${NC}"
    exit 1
fi

# Create a logs directory if it doesn't exist
mkdir -p logs/neural_ui_detector

# Check if the server is already running
PORT=8768
if netstat -atn | grep -q ":${PORT}.*LISTEN"; then
    echo -e "${RED}Warning: Port ${PORT} is already in use.${NC}"
    read -p "Do you want to kill the process and start a new server? (y/n): " response
    if [ "$response" = "y" ]; then
        # Kill the process using the port
        if [ "$(uname)" == "Darwin" ]; then
            # macOS
            PID=$(lsof -ti:${PORT})
        else
            # Linux
            PID=$(netstat -tulpn 2>/dev/null | grep ":${PORT}" | awk '{print $7}' | cut -d'/' -f1)
        fi
        
        if [ -n "$PID" ]; then
            echo -e "${BLUE}Killing process ${PID} on port ${PORT}...${NC}"
            kill -9 $PID
            sleep 1
        fi
    else
        echo -e "${BLUE}Using port ${PORT} without restarting the server.${NC}"
    fi
fi

# Start the server in the background
echo -e "${BLUE}Starting Neural UI Detector server on port ${PORT}...${NC}"
python neural_ui_detector_server.py --port ${PORT} > logs/neural_ui_detector/startup.log 2>&1 &
SERVER_PID=$!

# Wait for the server to start
echo -e "${BLUE}Waiting for server to initialize...${NC}"
sleep 2

# Check if the server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${GREEN}Neural UI Detector server started successfully with PID ${SERVER_PID}${NC}"
    
    # Save the PID to a file for later cleanup
    echo $SERVER_PID > logs/neural_ui_detector/server.pid
else
    echo -e "${RED}Failed to start Neural UI Detector server. Check logs/neural_ui_detector/startup.log for details.${NC}"
    exit 1
fi

# Open the test page in the default browser
echo -e "${BLUE}Opening test page in your default browser...${NC}"
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    open test_neural_ui_detector_fixed.html
elif [ "$(uname)" == "Linux" ]; then
    # Linux
    xdg-open test_neural_ui_detector_fixed.html
else
    # Windows or other
    start test_neural_ui_detector_fixed.html
fi

echo -e "${GREEN}Test environment started successfully!${NC}"
echo -e "${BLUE}To stop the server, run: kill $(cat logs/neural_ui_detector/server.pid)${NC}"
echo -e "${BLUE}Or press Ctrl+C to stop this script and the server.${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '${BLUE}Stopping Neural UI Detector server...${NC}'; kill $SERVER_PID; echo -e '${GREEN}Server stopped.${NC}'; exit 0" INT
echo "Server is running. Press Ctrl+C to stop."
while true; do
    sleep 1
done