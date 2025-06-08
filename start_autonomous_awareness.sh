#!/bin/bash

# Start Autonomous Awareness System
# This script starts the continuous autonomous system that monitors,
# generates suggestions, and executes plans without requiring constant
# user intervention.

echo "Starting Autonomous Awareness System..."

# Create necessary directories
mkdir -p logs/autonomous
mkdir -p cache/autonomous_awareness

# Set the process ID file
PID_FILE="pids/autonomous_awareness.pid"
mkdir -p pids

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Autonomous Awareness System is already running with PID $PID"
        echo "To restart, run stop_autonomous_awareness.sh first"
        exit 1
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Start the Python script
echo "Launching autonomous awareness system..."
python3 autonomous_awareness_system.py > logs/autonomous/stdout.log 2> logs/autonomous/stderr.log &
PID=$!

# Save the PID
echo $PID > "$PID_FILE"
echo "Autonomous Awareness System started with PID $PID"
echo "Logs are being written to logs/autonomous/"
echo "To stop the system, run stop_autonomous_awareness.sh"