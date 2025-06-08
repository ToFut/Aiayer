#\!/bin/bash
# Script to open the UI Elements Test Page

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================${NC}"
echo -e "${BLUE}         Opening UI Elements Test Page for Detection         ${NC}"
echo -e "${BLUE}==============================================================${NC}"

# Check if the Neural UI Detector server is running
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
    echo -e "${YELLOW}Please open the file manually:${NC} ui_test_elements.html"
    exit 1
fi

# Open the test page
echo -e "${GREEN}Opening UI Elements Test Page in browser...${NC}"
$BROWSER ui_test_elements.html

echo -e "${BLUE}==============================================================${NC}"
echo -e "${YELLOW}Instructions:${NC}"
echo -e "1. The test page contains various UI elements for detection testing"
echo -e "2. Return to the Neural UI Detector exam by clicking the 'Back' button"
echo -e "3. Use 'Detect UI Elements' in the exam to capture these elements"
echo -e "4. Then use 'Find & Click' to test interaction with specific elements"
echo -e "${BLUE}==============================================================${NC}"
