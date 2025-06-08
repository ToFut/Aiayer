#!/bin/bash
# Start Task Memory Dashboard Server
# This script launches the web-based dashboard for visualizing task memory metrics

# Ensure script is run from project root
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p logs/dashboard
mkdir -p web/dashboard/static/css
mkdir -p web/dashboard/static/js
mkdir -p web/dashboard/templates

# Check if dashboard server is already running
DASHBOARD_PID=$(ps aux | grep "python3.*start_dashboard_server.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$DASHBOARD_PID" ]; then
    echo "Dashboard server is already running with PID $DASHBOARD_PID"
    echo "Stopping existing dashboard server..."
    kill $DASHBOARD_PID
    sleep 2
fi

# Check if port 8081 is in use and force kill that process
PORT_PID=$(lsof -ti:8081)
if [ ! -z "$PORT_PID" ]; then
    echo "Port 8081 is in use by PID $PORT_PID. Stopping the process..."
    kill -9 $PORT_PID
    sleep 2
fi

# Start the dashboard server
echo "Starting Task Memory Dashboard Server..."
python3 start_dashboard_server.py > logs/dashboard_startup.log 2>&1 &
DASHBOARD_PID=$!

# Wait a moment to ensure server starts up
sleep 2

# Check if the server started successfully
if ps -p $DASHBOARD_PID > /dev/null; then
    echo "Dashboard server started successfully with PID $DASHBOARD_PID"
    echo "Server PID saved to pids/dashboard_server.pid"
    
    # Save PID to file for later reference
    mkdir -p pids
    echo $DASHBOARD_PID > pids/dashboard_server.pid
    
    echo "Access the dashboard at: http://localhost:8081"
else
    echo "Failed to start dashboard server. Check logs/dashboard_startup.log for details."
    exit 1
fi