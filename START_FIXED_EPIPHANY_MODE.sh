#!/bin/bash

# Start the fixed Epiphany mode connector
echo "Starting Fixed Epiphany Mode Connector..."
python3 fixed_epiphany_mode_connector.py &
EPIPHANY_PID=$!
echo $EPIPHANY_PID > pids/epiphany_connector.pid

echo "✅ Fixed Epiphany Mode Connector started on port 8765"
echo "🔍 To test it, run the overlay application with Epiphany Mode enabled"
echo "🛑 To stop it, run ./STOP_FIXED_EPIPHANY_MODE.sh"