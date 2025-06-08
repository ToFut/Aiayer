#\!/bin/bash
# This script runs the comprehensive DO button fix verification test
# It verifies that the entire chain from plan creation to execution works properly
# with the new plan persistence proxy in place

# Set up colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}    DO BUTTON FIX VERIFICATION TEST                      ${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs/do_button_fix

# Check if the system is running
echo -e "${YELLOW}Checking if the enhanced system is running...${NC}"

CHECK_PORT_8765=$(lsof -i:8765 | grep LISTEN)
CHECK_PORT_8766=$(lsof -i:8766 | grep LISTEN)
CHECK_PORT_8767=$(lsof -i:8767 | grep LISTEN)

if [ -z "$CHECK_PORT_8765" ] || [ -z "$CHECK_PORT_8766" ] || [ -z "$CHECK_PORT_8767" ]; then
    echo -e "${RED}Error: The enhanced system is not running completely.${NC}"
    echo -e "${RED}Please start the system using:${NC}"
    echo -e "${YELLOW}./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh${NC}"
    echo ""
    echo -e "${YELLOW}Port status:${NC}"
    echo -e "Port 8765 (WebSocket Server): ${CHECK_PORT_8765:+${GREEN}Running${NC}}${CHECK_PORT_8765:-${RED}Not running${NC}}"
    echo -e "Port 8766 (DO Button Proxy): ${CHECK_PORT_8766:+${GREEN}Running${NC}}${CHECK_PORT_8766:-${RED}Not running${NC}}"
    echo -e "Port 8767 (Brain Router): ${CHECK_PORT_8767:+${GREEN}Running${NC}}${CHECK_PORT_8767:-${RED}Not running${NC}}"
    exit 1
fi

echo -e "${GREEN}All required services are running. Starting the test...${NC}"

# Run the comprehensive test script
echo -e "${YELLOW}Running comprehensive DO button fix verification test...${NC}"
echo -e "${YELLOW}This will test the entire chain from plan creation to execution.${NC}"
echo -e "${YELLOW}Test results will be saved to a JSON file in the current directory.${NC}"
echo ""

python3 test_complete_do_button_fix.py | tee logs/do_button_fix/test_results.log

echo ""
echo -e "${GREEN}Test completed. Check the logs and JSON result file for details.${NC}"
echo -e "${BLUE}=========================================================${NC}"
