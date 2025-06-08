#\!/bin/bash
# Script to open the Advanced Neural UI Detector Examination tool

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================${NC}"
echo -e "${BLUE}     Opening Advanced Neural UI Detector Examination Tool     ${NC}"
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
    echo -e "${YELLOW}Please open the file manually:${NC} advanced_neural_ui_detector_exam.html"
    exit 1
fi

# Open the test page
echo -e "${GREEN}Opening Advanced Neural UI Detector Examination tool in browser...${NC}"
$BROWSER advanced_neural_ui_detector_exam.html

echo -e "${BLUE}==============================================================${NC}"
echo -e "${YELLOW}Instructions:${NC}"
echo -e "1. Click 'Connect' to connect to the Neural UI Detector server"
echo -e "2. Run individual tests or click 'Run All Tests' for comprehensive testing"
echo -e "3. Check results in the 'Results' tab and performance metrics in the 'Metrics' tab"
echo -e "4. Advanced testing options are available in the bottom section"
echo -e "${BLUE}==============================================================${NC}"
