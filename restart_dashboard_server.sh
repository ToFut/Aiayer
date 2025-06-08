#!/bin/bash
# Restart the dashboard server

# Kill any existing dashboard server processes
echo "Stopping existing dashboard server..."
pkill -f "dashboard_server.py"

# Wait for processes to stop
sleep 2

# Start the dashboard server
echo "Starting dashboard server..."
cd /Users/segevbin/Desktop/SensAI/Aiayer
python memory/dashboard_server.py &

# Wait for server to start
sleep 3

# Check if server is running
if pgrep -f "dashboard_server.py" > /dev/null; then
    echo "Dashboard server is now running"
    echo "You can access the dashboard at: http://localhost:8081/"
else
    echo "Failed to start dashboard server"
    exit 1
fi

# Check API endpoints
echo "Testing API endpoints..."
echo "Time-series API: "
curl -s http://localhost:8081/api/time-series | head -c 100
echo -e "\n\nMetrics API: "
curl -s http://localhost:8081/api/metrics | head -c 100
echo -e "\n"

echo "Dashboard restart complete!"