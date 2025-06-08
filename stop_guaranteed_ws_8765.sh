#\!/bin/bash
#
# stop_guaranteed_ws_8765.sh
#
# This script stops the WebSocket server on port 8765.
#

echo "Stopping WebSocket server on port 8765..."

# Check if PID file exists
if [ -f pids/ws_server_8765.pid ]; then
    pid=$(cat pids/ws_server_8765.pid)
    
    # Check if process is running
    if ps -p $pid > /dev/null; then
        echo "Stopping WebSocket server with PID: $pid"
        kill $pid
        sleep 1
        
        # Check if it is still running
        if ps -p $pid > /dev/null; then
            echo "Process still running, using force kill..."
            kill -9 $pid
            sleep 1
        fi
        
        if \! ps -p $pid > /dev/null; then
            echo "✅ WebSocket server stopped successfully"
        else
            echo "❌ Failed to stop WebSocket server"
        fi
    else
        echo "Process not running (PID: $pid)"
    fi
    
    # Remove PID file
    rm pids/ws_server_8765.pid
    echo "Removed PID file"
else
    echo "No PID file found at pids/ws_server_8765.pid"
fi

# Try to find and kill by port
if lsof -ti:8765 >/dev/null; then
    echo "Found WebSocket server running on port 8765, stopping..."
    lsof -ti:8765 | xargs kill -9
    echo "✅ WebSocket server stopped by port"
else
    echo "No WebSocket server found running on port 8765"
fi

echo "Done."
