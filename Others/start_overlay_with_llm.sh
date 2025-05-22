#\!/bin/bash
# Script to run the self-contained WebSocket LLM server

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Self-Contained LLM WebSocket Server...${NC}"

# Run the server start script
./run_self_contained_llm.sh

# Show information about connecting to the overlay
echo -e "\n${YELLOW}Important Information:${NC}"
echo -e "1. View server logs:       ${GREEN}tail -f logs/self_contained_llm_ws.log${NC}"
echo -e "2. To launch the overlay:  ${GREEN}cd overlay && npm run tauri dev${NC}"
echo -e "3. Overlay is configured to connect to ${BLUE}ws://localhost:8765${NC}"
echo -e "4. Check the overlay code to ensure it's using port 8765 for connection"

# Remind about fixing port in client if needed
echo -e "\n${YELLOW}IMPORTANT: If the overlay can't connect, check that these files use port 8765:${NC}"
echo -e "- ${BLUE}overlay/src/services/bridge.js${NC} (change line 15 if needed)"
echo -e "- ${BLUE}overlay/src/components/EnhancedNextGenChat.svelte${NC} (check line 8)"

echo -e "\n${GREEN}Server is now running\! Use the overlay to send messages to your local LLM.${NC}"
