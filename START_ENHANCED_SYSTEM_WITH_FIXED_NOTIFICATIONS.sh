#!/bin/bash
# START_ENHANCED_SYSTEM_WITH_FIXED_NOTIFICATIONS.sh
#
# Complete startup script for the Enhanced SensAI system with fixed DO button notifications
# This script launches all necessary components in the correct order:
# 1. Enterprise Backend Server (port 8767)
# 2. Neural UI Detector Server (port 8768)
# 3. DO Button Proxy Server (port 8766)
# 4. Overlay Chat (connects to Proxy Server on port 8766)
#
# This version includes the fixed notification system to ensure proper display in the overlay.

# Set up colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p logs/backend
mkdir -p logs/sensors
mkdir -p logs/websocket
mkdir -p logs/memory

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}     Starting Enhanced SensAI System with Fixed Notifications${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo

# Kill any existing processes that might conflict
echo -e "${YELLOW}Stopping any existing processes...${NC}"
./STOP_ENHANCED_SYSTEM.sh > /dev/null 2>&1
sleep 2

# Step 1: Start the Enterprise Backend Server (port 8767)
echo -e "${CYAN}Step 1: Starting Enterprise Backend Server (port 8767)${NC}"
python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend/backend_8767.pid
echo -e "${GREEN}✓ Enterprise Backend Server started with PID: $BACKEND_PID${NC}"
echo -e "  Log file: logs/backend/enhanced_enterprise_8767.log"
sleep 3

# Step 2: Start the Neural UI Detector Server (port 8768)
echo -e "${CYAN}Step 2: Starting Neural UI Detector Server (port 8768)${NC}"
python3 neural_ui_detector_server.py > logs/neural_ui_do_button.log 2>&1 &
NEURAL_UI_PID=$!
echo $NEURAL_UI_PID > logs/neural_ui_detector.pid
echo -e "${GREEN}✓ Neural UI Detector Server started with PID: $NEURAL_UI_PID${NC}"
echo -e "  Log file: logs/neural_ui_do_button.log"
sleep 3

# Step 3: Start the Ultimate DO Button Server (port 8765)
echo -e "${CYAN}Step 3: Starting Ultimate DO Button Server (port 8765)${NC}"
python3 ultimate_do_button_server.py > logs/ultimate_do_button_server.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > logs/do_button_server.pid
echo -e "${GREEN}✓ Ultimate DO Button Server started with PID: $DO_BUTTON_PID${NC}"
echo -e "  Log file: logs/ultimate_do_button_server.log"
sleep 3

# Step 4: Start the DO Button Proxy Server (port 8766)
echo -e "${CYAN}Step 4: Starting DO Button Proxy Server (port 8766)${NC}"
python3 fix_do_button_connection.py > logs/websocket/do_button_proxy.log 2>&1 &
PROXY_PID=$!
echo $PROXY_PID > logs/websocket/do_button_proxy.pid
echo -e "${GREEN}✓ DO Button Proxy Server started with PID: $PROXY_PID${NC}"
echo -e "  Log file: logs/websocket/do_button_proxy.log"
sleep 3

# Step 5: Start the Overlay Chat (connects to Proxy Server on port 8766)
echo -e "${CYAN}Step 5: Starting Overlay Chat${NC}"
cd overlay
python3 -m http.server 8080 > ../logs/http_server.log 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > ../logs/http_server.pid
echo -e "${GREEN}✓ HTTP Server started with PID: $HTTP_PID${NC}"
echo -e "  Log file: ../logs/http_server.log"
echo -e "  Overlay URL: http://localhost:8080"
cd ..

echo
echo -e "${BLUE}==================================================================${NC}"
echo -e "${GREEN}✓ All components started successfully!${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo
echo -e "The Enhanced SensAI System is now running with fixed notifications."
echo -e "You can access the overlay chat at: ${CYAN}http://localhost:8080${NC}"
echo
echo -e "WebSocket connections:"
echo -e "- Frontend connects to: ${CYAN}ws://localhost:8766${NC} (Proxy Server)"
echo -e "- Proxy Server connects to:"
echo -e "  * ${CYAN}ws://localhost:8765${NC} (Ultimate DO Button Server)"
echo -e "  * ${CYAN}ws://localhost:8768${NC} (Neural UI Detector Server)"
echo -e "- Both servers connect to: ${CYAN}ws://localhost:8767${NC} (Backend Server)"
echo
echo -e "To stop all components: ${YELLOW}./STOP_ENHANCED_SYSTEM.sh${NC}"
echo -e "${BLUE}==================================================================${NC}"