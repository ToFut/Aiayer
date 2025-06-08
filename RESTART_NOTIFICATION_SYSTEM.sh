#!/bin/bash
# Restart the notification system with a clean slate

# Set color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== RESTARTING NOTIFICATION SYSTEM ===${NC}"

# Stop the current notification system if running
echo -e "${YELLOW}Stopping any running notification system...${NC}"
./STOP_NOTIFICATION_SYSTEM.sh

# Make sure all the scripts are executable
chmod +x START_NOTIFICATION_SYSTEM.sh
chmod +x STOP_NOTIFICATION_SYSTEM.sh
chmod +x auto_suggestion_system.py
chmod +x direct_notification_test.py
chmod +x send_notification.py

# Start the notification system
echo -e "${GREEN}Starting notification system with a clean slate...${NC}"
./START_NOTIFICATION_SYSTEM.sh

# Send a test notification through each of the working ports
echo -e "${YELLOW}Sending test notifications to verify system...${NC}"

echo -e "${BLUE}Sending to port 8765...${NC}"
python send_notification.py "🔔 NOTIFICATION SYSTEM RESTARTED: Test to port 8765" --port 8765 --sound

echo -e "${BLUE}Sending to port 8767...${NC}"
python send_notification.py "🔔 NOTIFICATION SYSTEM RESTARTED: Test to port 8767" --port 8767 --sound

echo -e "${BLUE}Sending to port 8768...${NC}"
python send_notification.py "🔔 NOTIFICATION SYSTEM RESTARTED: Test to port 8768" --port 8768 --sound

echo ""
echo -e "${GREEN}Notification system restarted and tested!${NC}"
echo -e "${GREEN}The system will send periodic suggestions based on system activity.${NC}"
echo -e "${BLUE}To stop the system, run: ./STOP_NOTIFICATION_SYSTEM.sh${NC}"
echo -e "${BLUE}To send a manual notification, run: python send_notification.py \"Your message here\"${NC}"