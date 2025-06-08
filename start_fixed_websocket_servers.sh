#!/bin/bash
#
# Start Fixed WebSocket Servers with MASTER System
# This script starts all the fixed WebSocket servers and the MASTER system properly
#

# Create logs directory
mkdir -p logs/backend

# Ask user if they want to start the fixed WebSocket servers or the full MASTER system
echo "Please select which system to start:"
echo "1. Fixed WebSocket servers only (8765 and 8767)"
echo "2. Full MASTER system (recommended)"
read -p "Enter choice (1 or 2, default is 2): " CHOICE

if [ "$CHOICE" = "1" ]; then
    # Kill any existing servers on the ports we need
    echo "Stopping any existing WebSocket servers..."
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
    lsof -ti:8767 | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Start fixed WebSocket server on 8765 for overlay
    echo "Starting fixed WebSocket server on port 8765..."
    nohup python3 fixed_ws_server_8765.py > logs/fixed_ws_8765.log 2>&1 &
    FIXED_WS_PID=$!
    echo "Fixed WebSocket server started with PID: $FIXED_WS_PID"
    
    # Wait a moment to ensure it's started
    sleep 2
    
    # Start enhanced enterprise backend on 8767
    echo "Starting enhanced enterprise backend on port 8767..."
    nohup python3 enhanced_enterprise_backend_with_context.py > logs/enhanced_enterprise_backend.log 2>&1 &
    ENTERPRISE_PID=$!
    echo "Enhanced enterprise backend started with PID: $ENTERPRISE_PID"
    
    # Wait a moment to ensure it's started
    sleep 2
    
    # Check if servers are running
    echo "Checking if servers are running..."
    if ps -p $FIXED_WS_PID > /dev/null; then
        echo "✅ Fixed WebSocket server is running on port 8765"
    else
        echo "❌ Fixed WebSocket server failed to start on port 8765"
        echo "Check logs/fixed_ws_8765.log for errors"
    fi
    
    if ps -p $ENTERPRISE_PID > /dev/null; then
        echo "✅ Enhanced enterprise backend is running on port 8767"
    else
        echo "❌ Enhanced enterprise backend failed to start on port 8767"
        echo "Check logs/enhanced_enterprise_backend.log for errors"
    fi
    
    echo "WebSocket servers should now be available at:"
    echo "  ws://localhost:8765 - For overlay communication"
    echo "  ws://localhost:8767 - For enhanced enterprise backend"
    echo ""
    echo "To stop these servers, run: bash stop_fixed_websocket_servers.sh"
    
    # Save PIDs for stop script
    mkdir -p pids
    echo $FIXED_WS_PID > pids/fixed_ws_8765.pid
    echo $ENTERPRISE_PID > pids/enhanced_enterprise_backend.pid
else
    # Run the MASTER system
    echo "Starting the MASTER system with fixed WebSocket servers..."
    chmod +x START_MASTER_SYSTEM.sh
    ./START_MASTER_SYSTEM.sh
fi