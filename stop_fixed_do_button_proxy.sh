#!/bin/bash
#
# Stop Fixed DO Button Proxy
#
# This script stops the fixed minimal DO button proxy.
#

echo "Stopping Fixed DO Button Proxy..."

# Check if PID file exists
if [ -f pids/do_button_proxy.pid ]; then
    pid=$(cat pids/do_button_proxy.pid)
    
    # Check if process is running
    if ps -p $pid > /dev/null; then
        echo "Stopping proxy with PID: $pid"
        kill $pid
        sleep 1
        
        # Check if it's still running
        if ps -p $pid > /dev/null; then
            echo "Process still running, using force kill..."
            kill -9 $pid
            sleep 1
        fi
        
        if ! ps -p $pid > /dev/null; then
            echo "✅ Proxy stopped successfully"
        else
            echo "❌ Failed to stop proxy process"
        fi
    else
        echo "Process not running (PID: $pid)"
    fi
    
    # Remove PID file
    rm pids/do_button_proxy.pid
    echo "Removed PID file"
else
    echo "No PID file found at pids/do_button_proxy.pid"
fi

# Try to find and kill by port
if lsof -ti:8766 >/dev/null; then
    echo "Found proxy running on port 8766, stopping..."
    lsof -ti:8766 | xargs kill -9
    echo "✅ Proxy stopped by port"
else
    echo "No proxy process found running on port 8766"
fi

echo "Done."