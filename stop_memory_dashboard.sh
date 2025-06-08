#!/bin/bash
# Stop Neural Memory Dashboard

# Define log file
LOG_FILE="logs/memory_dashboard.log"

echo "Stopping Neural Memory Dashboard..." | tee -a $LOG_FILE

# Check if PID file exists
if [ -f "logs/memory_dashboard_server.pid" ]; then
    DASHBOARD_PID=$(cat logs/memory_dashboard_server.pid)
    
    # Check if process is running
    if ps -p $DASHBOARD_PID > /dev/null; then
        echo "Stopping Memory Dashboard Server (PID: $DASHBOARD_PID)..." | tee -a $LOG_FILE
        kill -15 $DASHBOARD_PID
        
        # Wait for process to terminate
        for i in {1..5}; do
            if ! ps -p $DASHBOARD_PID > /dev/null; then
                break
            fi
            echo "Waiting for process to terminate... ($i/5)" | tee -a $LOG_FILE
            sleep 1
        done
        
        # Force kill if still running
        if ps -p $DASHBOARD_PID > /dev/null; then
            echo "Process did not terminate gracefully. Forcing termination..." | tee -a $LOG_FILE
            kill -9 $DASHBOARD_PID
        fi
        
        echo "Memory Dashboard Server stopped." | tee -a $LOG_FILE
    else
        echo "Memory Dashboard Server (PID: $DASHBOARD_PID) is not running." | tee -a $LOG_FILE
    fi
    
    # Remove PID file
    rm logs/memory_dashboard_server.pid
else
    echo "Memory Dashboard Server PID file not found." | tee -a $LOG_FILE
    
    # Try to find and kill by port
    DASHBOARD_PORT=8082
    PORT_STATUS=$(lsof -i:$DASHBOARD_PORT | grep LISTEN)
    
    if [ ! -z "$PORT_STATUS" ]; then
        DASHBOARD_PID=$(echo $PORT_STATUS | awk '{print $2}')
        echo "Found Memory Dashboard Server running on port $DASHBOARD_PORT (PID: $DASHBOARD_PID)" | tee -a $LOG_FILE
        
        echo "Stopping Memory Dashboard Server..." | tee -a $LOG_FILE
        kill -15 $DASHBOARD_PID
        
        # Wait for process to terminate
        for i in {1..5}; do
            if ! ps -p $DASHBOARD_PID > /dev/null; then
                break
            fi
            echo "Waiting for process to terminate... ($i/5)" | tee -a $LOG_FILE
            sleep 1
        done
        
        # Force kill if still running
        if ps -p $DASHBOARD_PID > /dev/null; then
            echo "Process did not terminate gracefully. Forcing termination..." | tee -a $LOG_FILE
            kill -9 $DASHBOARD_PID
        fi
        
        echo "Memory Dashboard Server stopped." | tee -a $LOG_FILE
    else
        echo "No Memory Dashboard Server found running on port $DASHBOARD_PORT." | tee -a $LOG_FILE
    fi
fi

# Make sure the script has proper permissions
chmod +x start_memory_dashboard.sh

echo "Done." | tee -a $LOG_FILE