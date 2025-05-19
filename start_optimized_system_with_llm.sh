#!/bin/bash
# Enhanced optimized system with Enhanced LLM integration (context-aware, sensor and memory integration)
# This script extends start_optimized_system_fixed.sh to include the enhanced backend server with Ollama LLM

# Run the original start_optimized_system_fixed.sh script first
echo "Starting optimized system components..."
./start_optimized_system_fixed.sh

# Wait a moment for all components to initialize
sleep 2

# Start our fixed screen sensor
echo "Starting fixed screen sensor..."
./start_fixed_screen_sensor.sh

# Start the bridge server (critical component for message routing)
echo "Starting fixed bridge server for message routing..."
mkdir -p logs
python3 fixed_bridge_server.py > logs/fixed_bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID: $BRIDGE_PID"

# Wait for bridge to initialize
sleep 3

# Now start the enhanced backend server with Ollama Enhanced LLM integration
echo "Starting enhanced backend server with Ollama Enhanced LLM integration..."
./start_enhanced_backend.sh

echo -e "\n\033[0;32mComplete system is now running with all components initialized!\033[0m"
echo -e "\033[0;34mFrontend can connect to ws://localhost:8765 to communicate with the backend\033[0m"
echo -e "\033[0;34mBackend will manage requests and use Enhanced Ollama LLM for context-aware responses\033[0m"
echo -e "\033[0;34mMemory system will provide context for more relevant responses\033[0m"

# Print information about monitoring logs
echo -e "\n\033[0;33mTo monitor the system:\033[0m"
echo "tail -f logs/backend_server.log    # Backend server logs"
echo "tail -f logs/sensors/*.log         # Sensor logs"
echo "tail -f logs/memory/*.log          # Memory system logs"