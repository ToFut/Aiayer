#!/bin/bash
# Update the START_ENHANCED_SYSTEM.sh script to use the real input DO button executor

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Updating START_ENHANCED_SYSTEM.sh to use the real input DO button executor...${NC}"

# Backup the original file
BACKUP_FILE="START_ENHANCED_SYSTEM.sh.bak.$(date +%Y%m%d)"
cp START_ENHANCED_SYSTEM.sh $BACKUP_FILE
echo -e "${GREEN}Original backed up to $BACKUP_FILE${NC}"

# Find the part that starts the WebSocket server (current DO button handler)
DO_BUTTON_SECTION=$(grep -n "Starting DO button WebSocket server" START_ENHANCED_SYSTEM.sh | cut -d: -f1)

if [ -z "$DO_BUTTON_SECTION" ]; then
  DO_BUTTON_SECTION=$(grep -n "Adding ultimate DO button server" START_ENHANCED_SYSTEM.sh | cut -d: -f1)
fi

if [ -z "$DO_BUTTON_SECTION" ]; then
  echo -e "${RED}Could not find DO button section in START_ENHANCED_SYSTEM.sh${NC}"
  exit 1
fi

# Create a temporary file with the updated content
TMP_FILE=$(mktemp)

# Extract the part before the DO button section
head -n $(($DO_BUTTON_SECTION - 1)) START_ENHANCED_SYSTEM.sh > $TMP_FILE

# Add our new DO button executor
cat << 'EOF' >> $TMP_FILE
 Adding real input DO button server for guaranteed functionality with REAL MOUSE and KEYBOARD input...
 chmod +x real_do_button_executor_with_real_input.py
 
 # Stop any existing WebSocket servers on port 8765
 if lsof -ti:8765 >/dev/null; then
   echo "Stopping existing WebSocket server on port 8765..."
   lsof -ti:8765 | xargs kill -9
 fi
 
 # Start the real input DO button executor
 echo "Starting REAL INPUT DO Button Executor (with real mouse/keyboard actions)..."
 python3 real_do_button_executor_with_real_input.py > logs/websocket/real_do_button_executor.log 2>&1 &
 echo $! > pids/real_do_button_executor.pid
 
 # Wait for the server to start
 sleep 2
 if lsof -ti:8765 >/dev/null; then
   echo "✅ Real input DO Button Server is listening on port 8765"
 else
   echo "❌ Failed to start DO Button Server"
   exit 1
 fi
EOF

# Find the end of the DO button section
END_SECTION=$(tail -n +$DO_BUTTON_SECTION START_ENHANCED_SYSTEM.sh | grep -n "Testing DO button WebSocket server" | head -1 | cut -d: -f1)

if [ -z "$END_SECTION" ]; then
  END_SECTION=$(tail -n +$DO_BUTTON_SECTION START_ENHANCED_SYSTEM.sh | grep -n "DO Button Server" | head -1 | cut -d: -f1)
fi

if [ -n "$END_SECTION" ]; then
  # Calculate the line number in the original file
  END_LINE=$(($DO_BUTTON_SECTION + $END_SECTION - 1))
  # Append the rest of the file after the DO button server test
  tail -n +$END_LINE START_ENHANCED_SYSTEM.sh >> $TMP_FILE
else
  # If we can't find the end section, just append from 10 lines after the start section
  tail -n +$(($DO_BUTTON_SECTION + 10)) START_ENHANCED_SYSTEM.sh >> $TMP_FILE
fi

# Replace the original file with our updated version
mv $TMP_FILE START_ENHANCED_SYSTEM.sh
chmod +x START_ENHANCED_SYSTEM.sh

echo -e "${GREEN}✅ START_ENHANCED_SYSTEM.sh updated to use the real input DO button executor${NC}"
echo -e "${GREEN}✅ Original backed up to $BACKUP_FILE${NC}"
echo -e "${GREEN}✅ The system will now perform REAL mouse and keyboard actions when using the DO button${NC}"
echo -e ""
echo -e "${YELLOW}To start the updated system, run:${NC}"
echo -e "  ${BLUE}./STOP_ENHANCED_SYSTEM.sh${NC}"
echo -e "  ${BLUE}./START_ENHANCED_SYSTEM.sh${NC}"