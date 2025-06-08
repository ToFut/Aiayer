#!/bin/bash
# Start Neural Memory Dashboard

# Define log file
LOG_FILE="logs/memory_dashboard.log"
DASHBOARD_PORT=8082

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Neural Memory Dashboard..."
echo "$(date): Starting Neural Memory Dashboard" >> $LOG_FILE

# Check if required Python modules are installed
echo "Checking dependencies..." >> $LOG_FILE
python3 -c "import flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required dependencies..." | tee -a $LOG_FILE
    pip3 install flask flask-cors
fi

# Check if port is already in use
PORT_STATUS=$(lsof -i:$DASHBOARD_PORT | grep LISTEN)
if [ ! -z "$PORT_STATUS" ]; then
    echo "Port $DASHBOARD_PORT is already in use. Stopping existing process..." | tee -a $LOG_FILE
    PID=$(echo $PORT_STATUS | awk '{print $2}')
    kill -9 $PID
    sleep 2
fi

# Start the dashboard server
echo "Starting Memory Dashboard Server on port $DASHBOARD_PORT..." | tee -a $LOG_FILE
python3 memory/memory_dashboard_server.py > logs/memory_dashboard_server.log 2>&1 &
DASHBOARD_PID=$!

# Save PID to file for later termination
echo $DASHBOARD_PID > logs/memory_dashboard_server.pid
echo "Memory Dashboard Server started with PID: $DASHBOARD_PID" | tee -a $LOG_FILE

# Wait a moment for the server to start
sleep 2

# Check if server started successfully
if ps -p $DASHBOARD_PID > /dev/null; then
    echo "Memory Dashboard Server started successfully." | tee -a $LOG_FILE
    echo "Opening dashboard in your browser..."
    
    # Try to open the dashboard in the browser (platform-dependent)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:$DASHBOARD_PORT/memory"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:$DASHBOARD_PORT/memory" &>/dev/null || echo "Please open http://localhost:$DASHBOARD_PORT/memory in your browser"
    else
        echo "Please open http://localhost:$DASHBOARD_PORT/memory in your browser"
    fi
    
    echo "Dashboard is running at: http://localhost:$DASHBOARD_PORT/memory"
    echo "Press Ctrl+C to stop the dashboard server"
    
    # Keep script running to show logs and allow for Ctrl+C
    tail -f logs/memory_dashboard_server.log
else
    echo "Failed to start Memory Dashboard Server." | tee -a $LOG_FILE
    echo "Check logs/memory_dashboard_server.log for details."
fi