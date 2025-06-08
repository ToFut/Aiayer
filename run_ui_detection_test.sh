#!/bin/bash

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Neural UI Detector Test Suite ====${NC}"

# Create cache directory if it doesn't exist
mkdir -p cache/neural_ui_detector

# Check for required files
if [ ! -f "neural_ui_detector_server.py" ]; then
    echo -e "${RED}Error: neural_ui_detector_server.py not found in the current directory.${NC}"
    exit 1
fi

if [ ! -f "ui_test_elements.html" ]; then
    echo -e "${RED}Error: ui_test_elements.html not found in the current directory.${NC}"
    exit 1
fi

if [ ! -f "direct_ui_test.py" ]; then
    echo -e "${RED}Error: direct_ui_test.py not found in the current directory.${NC}"
    exit 1
fi

# Parse command-line arguments
START_SERVER=true
SPECIFIC_ELEMENTS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-server)
            START_SERVER=false
            shift
            ;;
        --elements=*)
            SPECIFIC_ELEMENTS="${1#*=}"
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            echo "Usage: $0 [--no-server] [--elements=id1,id2,...]"
            exit 1
            ;;
    esac
done

# Create logs directory
mkdir -p logs/neural_ui_detector

# Check if we need to start the server
if [ "$START_SERVER" = true ]; then
    # Check if the server is already running
    if lsof -i:8768 -sTCP:LISTEN >/dev/null 2>&1; then
        echo -e "${YELLOW}Neural UI Detector server is already running on port 8768.${NC}"
        read -p "Do you want to restart it? (y/n): " RESTART
        if [ "$RESTART" = "y" ]; then
            echo -e "${BLUE}Stopping existing Neural UI Detector server...${NC}"
            kill $(lsof -ti:8768) 2>/dev/null
            sleep 2
            
            echo -e "${BLUE}Starting Neural UI Detector server...${NC}"
            python neural_ui_detector_server.py > logs/neural_ui_detector/server_run.log 2>&1 &
            SERVER_PID=$!
            echo $SERVER_PID > logs/neural_ui_detector/server.pid
            sleep 5
        fi
    else
        echo -e "${BLUE}Starting Neural UI Detector server...${NC}"
        python neural_ui_detector_server.py > logs/neural_ui_detector/server_run.log 2>&1 &
        SERVER_PID=$!
        echo $SERVER_PID > logs/neural_ui_detector/server.pid
        sleep 5
    fi
fi

# Build the command
CMD="python direct_ui_test.py --start-server"
if [ -n "$SPECIFIC_ELEMENTS" ]; then
    CMD="$CMD --elements=$SPECIFIC_ELEMENTS"
fi

# Run the test
echo -e "${BLUE}Running UI element tests...${NC}"
echo -e "${BLUE}Command: $CMD${NC}"
$CMD

# Check the result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests completed successfully!${NC}"
else
    echo -e "${RED}Tests failed. Check the logs for details.${NC}"
fi

# Ask if the user wants to kill the server
if [ "$START_SERVER" = true ]; then
    read -p "Do you want to stop the Neural UI Detector server? (y/n): " STOP_SERVER
    if [ "$STOP_SERVER" = "y" ]; then
        if [ -f "logs/neural_ui_detector/server.pid" ]; then
            SERVER_PID=$(cat logs/neural_ui_detector/server.pid)
            echo -e "${BLUE}Stopping Neural UI Detector server (PID: $SERVER_PID)...${NC}"
            kill $SERVER_PID 2>/dev/null
            rm logs/neural_ui_detector/server.pid
        else
            echo -e "${BLUE}Stopping all Neural UI Detector server processes...${NC}"
            kill $(lsof -ti:8768) 2>/dev/null
        fi
    fi
fi

echo -e "${BLUE}Test run complete.${NC}"