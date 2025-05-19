#!/bin/bash
# Enhanced optimized system with LocalLLM integration
# This script extends start_optimized_system_fixed.sh to include the enhanced backend server

# Run the original start_optimized_system_fixed.sh script first
echo "Starting optimized system components..."
./start_optimized_system_fixed.sh

# Wait a moment for all components to initialize
sleep 2

# Now start the enhanced backend server with LocalLLM integration
echo "Starting enhanced backend server with LocalLLM integration..."
./start_enhanced_backend.sh

echo -e "\n\033[0;32mComplete system is now running with all components initialized!\033[0m"
echo -e "\033[0;34mFrontend can connect to ws://localhost:8765 to communicate with the backend\033[0m"
echo -e "\033[0;34mBackend will manage requests and use LocalLLM for generating responses\033[0m"
echo -e "\033[0;34mMemory system will provide context for more relevant responses\033[0m"

# Print information about monitoring logs
echo -e "\n\033[0;33mTo monitor the system:\033[0m"
echo "tail -f logs/backend_server.log    # Backend server logs"
echo "tail -f logs/sensors/*.log         # Sensor logs"
echo "tail -f logs/memory/*.log          # Memory system logs"