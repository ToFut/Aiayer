#!/bin/bash
# Start the real input DO button executor

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Real DO Button Executor with REAL INPUT...${NC}"

# Make sure the script is executable
chmod +x real_do_button_executor_with_real_input.py

# Ensure the directories exist
mkdir -p logs/websocket
mkdir -p pids

# Stop any existing WebSocket servers on port 8765
echo -e "${YELLOW}Stopping any existing WebSocket servers on port 8765...${NC}"
if lsof -ti:8765 >/dev/null; then
  lsof -ti:8765 | xargs kill -9
  echo -e "${GREEN}Existing WebSocket server stopped${NC}"
else
  echo -e "${YELLOW}No existing WebSocket server found${NC}"
fi

# Stop any existing real DO button executors
if [ -f "pids/real_do_button_executor.pid" ]; then
  PID=$(cat pids/real_do_button_executor.pid)
  if ps -p $PID > /dev/null; then
    echo -e "${YELLOW}Stopping existing real DO button executor (PID: $PID)${NC}"
    kill -9 $PID
  fi
  rm -f pids/real_do_button_executor.pid
fi

# Start the executor in the background
echo -e "${GREEN}Starting Real DO Button Executor with REAL INPUT...${NC}"
python3 real_do_button_executor_with_real_input.py > logs/websocket/real_do_button_executor_with_real_input.log 2>&1 &

# Save PID
echo $! > pids/real_do_button_executor.pid
echo -e "${GREEN}Real DO Button Executor started with PID: $!${NC}"

# Verify that the server is running
sleep 2
if lsof -ti:8765 >/dev/null; then
  echo -e "${GREEN}✅ Real DO Button Executor is running on port 8765${NC}"
  echo -e "${GREEN}✅ DO button clicks will now perform REAL mouse and keyboard actions${NC}"
  echo -e "${YELLOW}⚠️ IMPORTANT: Emergency shutdown available with Ctrl+1${NC}"
  echo -e "${BLUE}Log file: logs/websocket/real_do_button_executor_with_real_input.log${NC}"
else
  echo -e "${RED}❌ Failed to start Real DO Button Executor${NC}"
  echo -e "${YELLOW}Check logs for details: logs/websocket/real_do_button_executor_with_real_input.log${NC}"
  exit 1
fi

echo -e "${GREEN}Setup complete. Plans created by the LLM will now be executed with REAL input when the DO button is clicked.${NC}"