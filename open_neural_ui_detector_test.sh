#\!/bin/bash
# Script to open the Neural UI Detector test page in the browser

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================${NC}"
echo -e "${BLUE}      Opening Neural UI Detector Test Page (Port 8768)       ${NC}"
echo -e "${BLUE}==============================================================${NC}"

# Check if the server is running
SERVER_RUNNING=false

if command -v lsof &> /dev/null; then
    if lsof -i:8768 | grep LISTEN &> /dev/null; then
        SERVER_RUNNING=true
    fi
elif command -v netstat &> /dev/null; then
    if netstat -an | grep 8768 | grep LISTEN &> /dev/null; then
        SERVER_RUNNING=true
    fi
fi

if [ "$SERVER_RUNNING" = true ]; then
    echo -e "${GREEN}Neural UI Detector server is running on port 8768${NC}"
else
    echo -e "${RED}Neural UI Detector server is NOT running on port 8768${NC}"
    echo -e "${YELLOW}Starting the server first...${NC}"
    
    # Try to start the server
    if [ -f "start_neural_ui_detector.sh" ]; then
        sh start_neural_ui_detector.sh &
        sleep 3 # Give it time to start
    else
        echo -e "${RED}Could not find start_neural_ui_detector.sh script${NC}"
        echo -e "${YELLOW}Please start the server manually before opening the test page${NC}"
    fi
fi

# Determine which browser to use
BROWSER=""

if command -v open &> /dev/null; then
    # macOS
    BROWSER="open"
elif command -v xdg-open &> /dev/null; then
    # Linux
    BROWSER="xdg-open"
elif command -v start &> /dev/null; then
    # Windows
    BROWSER="start"
else
    echo -e "${RED}Could not find a browser to open the test page${NC}"
    echo -e "${YELLOW}Please open the file manually:${NC} test_neural_ui_detector_simple.html"
    exit 1
fi

# Open the test page
echo -e "${GREEN}Opening test page in browser...${NC}"
$BROWSER test_neural_ui_detector_simple.html

echo -e "${BLUE}==============================================================${NC}"
echo -e "${YELLOW}Instructions:${NC}"
echo -e "1. Click 'Connect' to connect to the Neural UI Detector server"
echo -e "2. Click 'Send Ping' to test the connection"
echo -e "3. Click 'Detect UI Elements' to detect UI elements on the screen"
echo -e "${BLUE}==============================================================${NC}"
