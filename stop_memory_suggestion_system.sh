#!/bin/bash
# stop_memory_suggestion_system.sh
#
# Stops the proactive memory-aware suggestion system

# Set base directory
BASE_DIR=$(dirname "$0")
cd "$BASE_DIR" || exit 1

# Check if the system is running
if [ ! -f "pids/memory_suggestion_monitor.pid" ]; then
    echo "Memory suggestion monitor is not running"
    exit 0
fi

# Get the PID
PID=$(cat pids/memory_suggestion_monitor.pid)

# Check if process exists
if ! ps -p "$PID" > /dev/null; then
    echo "Memory suggestion monitor is not running (stale PID file)"
    rm -f pids/memory_suggestion_monitor.pid
    exit 0
fi

# Stop the process
echo "Stopping memory suggestion monitor (PID: $PID)..."
kill "$PID"

# Wait for process to stop
TIMEOUT=10
COUNT=0
while ps -p "$PID" > /dev/null && [ $COUNT -lt $TIMEOUT ]; do
    sleep 1
    COUNT=$((COUNT + 1))
done

# Check if process is still running
if ps -p "$PID" > /dev/null; then
    echo "Process did not stop gracefully, forcing termination..."
    kill -9 "$PID"
    sleep 1
fi

# Remove PID file
rm -f pids/memory_suggestion_monitor.pid

echo "Memory suggestion monitor stopped successfully"
exit 0