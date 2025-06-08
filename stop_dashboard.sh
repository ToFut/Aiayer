#!/bin/bash
# Stop Task Memory Dashboard Server
# This script stops the web-based dashboard for task memory metrics

# Ensure script is run from project root
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f pids/dashboard_server.pid ]; then
    DASHBOARD_PID=$(cat pids/dashboard_server.pid)
    
    # Check if process is still running
    if ps -p $DASHBOARD_PID > /dev/null; then
        echo "Stopping dashboard server with PID $DASHBOARD_PID..."
        kill $DASHBOARD_PID
        
        # Wait for process to terminate
        sleep 2
        
        # Check if it's still running and force kill if necessary
        if ps -p $DASHBOARD_PID > /dev/null; then
            echo "Dashboard server didn't terminate gracefully, forcing termination..."
            kill -9 $DASHBOARD_PID
        fi
        
        echo "Dashboard server stopped successfully."
    else
        echo "Dashboard server with PID $DASHBOARD_PID is not running."
    fi
    
    # Remove PID file
    rm pids/dashboard_server.pid
else
    # Try to find dashboard server process if PID file doesn't exist
    DASHBOARD_PID=$(ps aux | grep "python3.*start_dashboard_server.py" | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        echo "Found dashboard server with PID $DASHBOARD_PID, stopping it..."
        kill $DASHBOARD_PID
        
        # Wait for process to terminate
        sleep 2
        
        # Check if it's still running and force kill if necessary
        if ps -p $DASHBOARD_PID > /dev/null; then
            echo "Dashboard server didn't terminate gracefully, forcing termination..."
            kill -9 $DASHBOARD_PID
        fi
        
        echo "Dashboard server stopped successfully."
    else
        echo "No running dashboard server found."
    fi
fi