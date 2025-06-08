#!/bin/bash
# Stop the automatic notification system

# Set color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== STOPPING NOTIFICATION SYSTEM ===${NC}"

# Create directory for PID files if it doesn't exist
mkdir -p pids

# Check if PID file exists
if [ -f ./pids/notification_system.pid ]; then
    PID=$(cat ./pids/notification_system.pid)
    
    # Check if process is running
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Stopping notification system with PID: $PID${NC}"
        kill $PID
        sleep 1
        
        # Double-check if process was killed
        if ps -p $PID > /dev/null; then
            echo -e "${RED}Process still running, sending SIGKILL...${NC}"
            kill -9 $PID
            sleep 1
        fi
        
        # Final check
        if ! ps -p $PID > /dev/null; then
            echo -e "${GREEN}Notification system stopped successfully${NC}"
            rm ./pids/notification_system.pid
        else
            echo -e "${RED}Failed to stop notification system${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Process with PID $PID is not running${NC}"
        rm ./pids/notification_system.pid
    fi
else
    # Check if any auto_suggestion_system.py process is running
    RUNNING_PID=$(pgrep -f "python.*auto_suggestion_system.py")
    
    if [ -n "$RUNNING_PID" ]; then
        echo -e "${YELLOW}Found notification system running with PID: $RUNNING_PID${NC}"
        kill $RUNNING_PID
        sleep 1
        
        # Double-check if process was killed
        if ps -p $RUNNING_PID > /dev/null; then
            echo -e "${RED}Process still running, sending SIGKILL...${NC}"
            kill -9 $RUNNING_PID
            sleep 1
        fi
        
        # Final check
        if ! ps -p $RUNNING_PID > /dev/null; then
            echo -e "${GREEN}Notification system stopped successfully${NC}"
        else
            echo -e "${RED}Failed to stop notification system${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}No notification system found running${NC}"
    fi
fi

echo -e "${BLUE}To restart the notification system, run: ./START_NOTIFICATION_SYSTEM.sh${NC}"