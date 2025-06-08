#!/bin/bash
# Check the status of all system components

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Enhanced System with Real Input DO Button Status ===${NC}"
echo ""

# Check Backend
if lsof -i :8767 > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Enhanced Enterprise Backend is running (port 8767)${NC}"
  BACKEND_PID=$(lsof -ti:8767)
  echo -e "   PID: $BACKEND_PID"
else
  echo -e "${RED}❌ Enhanced Enterprise Backend is NOT running${NC}"
fi

# Check DO Button Executor
if lsof -i :8765 > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Real Input DO Button Executor is running (port 8765)${NC}"
  DO_BUTTON_PID=$(lsof -ti:8765)
  echo -e "   PID: $DO_BUTTON_PID"
else
  echo -e "${RED}❌ Real Input DO Button Executor is NOT running${NC}"
fi

# Check Process Sensor
if [ -f "pids/process_sensor.pid" ]; then
  PROCESS_PID=$(cat pids/process_sensor.pid)
  if ps -p $PROCESS_PID > /dev/null; then
    echo -e "${GREEN}✅ Process Sensor is running${NC}"
    echo -e "   PID: $PROCESS_PID"
  else
    echo -e "${RED}❌ Process Sensor is NOT running (stale PID file)${NC}"
  fi
else
  echo -e "${YELLOW}⚠️ Process Sensor PID file not found${NC}"
fi

# Check Total Screen Analyzer
if [ -f "pids/total_screen_analyzer.pid" ]; then
  SCREEN_PID=$(cat pids/total_screen_analyzer.pid)
  if ps -p $SCREEN_PID > /dev/null; then
    echo -e "${GREEN}✅ Total Screen Analyzer is running${NC}"
    echo -e "   PID: $SCREEN_PID"
  else
    echo -e "${RED}❌ Total Screen Analyzer is NOT running (stale PID file)${NC}"
  fi
else
  echo -e "${YELLOW}⚠️ Total Screen Analyzer PID file not found${NC}"
fi

# Check Smart Memory Feeder
if [ -f "pids/smart_memory_feeder.pid" ]; then
  MEMORY_PID=$(cat pids/smart_memory_feeder.pid)
  if ps -p $MEMORY_PID > /dev/null; then
    echo -e "${GREEN}✅ Smart Memory Feeder is running${NC}"
    echo -e "   PID: $MEMORY_PID"
  else
    echo -e "${RED}❌ Smart Memory Feeder is NOT running (stale PID file)${NC}"
  fi
else
  echo -e "${YELLOW}⚠️ Smart Memory Feeder PID file not found${NC}"
fi

echo ""
echo -e "${BLUE}=== System Log Status ===${NC}"

# Check recent log activity
echo -e "${YELLOW}Recent DO Button Executor Log:${NC}"
if [ -f "logs/websocket/real_do_button_executor.log" ]; then
  tail -n 5 logs/websocket/real_do_button_executor.log
else
  echo -e "${RED}Log file not found${NC}"
fi

echo ""
echo -e "${YELLOW}Recent Backend Log:${NC}"
if [ -f "logs/backend/enhanced_enterprise_8767.log" ]; then
  tail -n 5 logs/backend/enhanced_enterprise_8767.log
else
  echo -e "${RED}Log file not found${NC}"
fi

echo ""
echo -e "${BLUE}=== Usage Information ===${NC}"
echo -e "${GREEN}To stop the system:${NC} ./stop_real_do_button_system.sh"
echo -e "${GREEN}To start individual components:${NC}"
echo -e "  Real DO Button: ./start_real_input_executor.sh"
echo -e "  Backend: python3 enhanced_enterprise_backend_with_context.py"
echo -e "  Process Sensor: python3 sensors/enhanced_fixed_process_sensor.py"
echo -e "  Screen Analyzer: python3 sensors/total_screen_analyzer.py"
echo -e "  Memory Feeder: python3 smart_memory_feeder.py"