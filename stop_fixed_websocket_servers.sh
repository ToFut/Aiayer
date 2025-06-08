#!/bin/bash
#
# Stop Fixed WebSocket Servers
# This script stops all the fixed WebSocket servers
#

echo "Stopping WebSocket servers..."

# Check for fixed WebSocket server on 8765
if [ -f "pids/fixed_ws_8765.pid" ]; then
    FIXED_WS_PID=$(cat pids/fixed_ws_8765.pid)
    if ps -p $FIXED_WS_PID > /dev/null; then
        echo "Stopping fixed WebSocket server (PID: $FIXED_WS_PID)..."
        kill -15 $FIXED_WS_PID 2>/dev/null || kill -9 $FIXED_WS_PID 2>/dev/null
        echo "✅ Fixed WebSocket server stopped"
    else
        echo "Fixed WebSocket server was not running"
    fi
    rm -f pids/fixed_ws_8765.pid
else
    echo "No PID file found for fixed WebSocket server"
    # Try to kill by port
    lsof -ti:8765 | xargs kill -9 2>/dev/null
fi

# Check for enhanced enterprise backend on 8767
if [ -f "pids/enhanced_enterprise_backend.pid" ]; then
    ENTERPRISE_PID=$(cat pids/enhanced_enterprise_backend.pid)
    if ps -p $ENTERPRISE_PID > /dev/null; then
        echo "Stopping enhanced enterprise backend (PID: $ENTERPRISE_PID)..."
        kill -15 $ENTERPRISE_PID 2>/dev/null || kill -9 $ENTERPRISE_PID 2>/dev/null
        echo "✅ Enhanced enterprise backend stopped"
    else
        echo "Enhanced enterprise backend was not running"
    fi
    rm -f pids/enhanced_enterprise_backend.pid
else
    echo "No PID file found for enhanced enterprise backend"
    # Try to kill by port
    lsof -ti:8767 | xargs kill -9 2>/dev/null
fi

echo "All WebSocket servers stopped"