#!/bin/bash

# Run DO Button Test Framework
# This script launches the comprehensive DO button testing framework

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    DO Button Testing Framework         ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Create directory for logs
mkdir -p logs/exams
mkdir -p test_screenshots

# Check for required dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not found. Please install Python 3.${NC}"
    exit 1
fi

# Check for required Python packages
echo -e "${YELLOW}Checking Python packages...${NC}"
python3 -c "import websockets" &> /dev/null || { 
    echo -e "${YELLOW}websockets package not found. Installing...${NC}"
    pip3 install websockets
}

python3 -c "import PIL" &> /dev/null || { 
    echo -e "${YELLOW}PIL (Pillow) package not found. Installing...${NC}"
    pip3 install pillow
}

# Generate test screenshots if they don't exist
echo -e "${YELLOW}Checking for test screenshots...${NC}"
screenshot_count=$(ls -1 test_screenshots/*.png 2>/dev/null | wc -l)
if [ "$screenshot_count" -lt 5 ]; then
    echo -e "${YELLOW}Generating test screenshots...${NC}"
    python3 generate_test_screenshots.py
else
    echo -e "${GREEN}Found existing test screenshots.${NC}"
fi

# Stop any existing servers
echo -e "${YELLOW}Checking for existing test servers...${NC}"
pkill -f "advanced_agent_do_button_exam.py" &> /dev/null
sleep 1

# Start the test server
echo -e "${GREEN}Starting DO Button Test Server...${NC}"
python3 advanced_agent_do_button_exam.py --debug --open-browser &

# Save server PID
server_pid=$!
echo $server_pid > "pids/do_button_test_server.pid"

echo -e "${GREEN}Server started with PID: $server_pid${NC}"
echo -e "${GREEN}Test interface opened in browser.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server when done.${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '${YELLOW}Stopping server...${NC}'; kill $server_pid 2>/dev/null; exit 0" INT TERM
wait $server_pid