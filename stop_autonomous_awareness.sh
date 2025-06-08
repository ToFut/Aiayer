#!/bin/bash

# Stop Autonomous Awareness System
# This script stops the continuous autonomous system.

echo "Stopping Autonomous Awareness System..."

# Set the process ID file
PID_FILE="pids/autonomous_awareness.pid"

# Check if running
if [ ! -f "$PID_FILE" ]; then
    echo "Autonomous Awareness System is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")
if ! ps -p $PID > /dev/null; then
    echo "Process with PID $PID not found, removing stale PID file"
    rm "$PID_FILE"
    exit 0
fi

# Send SIGTERM to allow graceful shutdown with proper persistence
echo "Sending termination signal to PID $PID..."
kill -TERM $PID

# Wait for it to exit
MAX_WAIT=10
WAIT_COUNT=0
while ps -p $PID > /dev/null && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    echo "Waiting for process to exit ($WAIT_COUNT/$MAX_WAIT)..."
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

# Force kill if still running
if ps -p $PID > /dev/null; then
    echo "Process still running after $MAX_WAIT seconds, forcing termination..."
    kill -9 $PID
    sleep 1
fi

# Remove PID file
rm "$PID_FILE"
echo "Autonomous Awareness System stopped"