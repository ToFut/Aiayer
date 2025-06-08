#!/bin/bash
# Start the automatic notification system

# Set color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== STARTING NOTIFICATION SYSTEM ===${NC}"
echo -e "${YELLOW}This script starts a system that sends action suggestions to the overlay chat${NC}"
echo -e "${YELLOW}These notifications will bypass the LLM and plan persistence systems${NC}"
echo ""

# Make sure directories exist
mkdir -p logs

# Check if system is already running
if pgrep -f "python.*auto_suggestion_system.py" > /dev/null; then
    echo -e "${RED}Notification system is already running${NC}"
    echo "If you want to restart, run STOP_NOTIFICATION_SYSTEM.sh first"
    exit 1
fi

# Run the immediate notification test to verify connection
echo -e "${YELLOW}Running initial notification test...${NC}"
python direct_notification_test.py

# Start the auto suggestion system in the background
echo -e "${GREEN}Starting automatic suggestion system...${NC}"
nohup python auto_suggestion_system.py > logs/notification_system.log 2>&1 &
PID=$!

# Save PID
echo $PID > ./pids/notification_system.pid
echo -e "${GREEN}Notification system started with PID: $PID${NC}"
echo -e "Logs are available at: logs/notification_system.log"
echo ""
echo -e "${BLUE}System will periodically send UI-based action suggestions${NC}"
echo -e "${BLUE}To stop the system, run: ./STOP_NOTIFICATION_SYSTEM.sh${NC}"