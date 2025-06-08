#!/bin/bash
# Restart Ultimate DO Button Server with the NextGen suggestion fix applied

# First kill any existing DO button server
echo "Stopping existing DO button server..."
pid_file="pids/ultimate_do_button_server.pid"
if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if ps -p "$pid" > /dev/null; then
        echo "Killing process $pid..."
        kill -9 "$pid"
        sleep 1
    else
        echo "Process $pid is not running"
    fi
    rm "$pid_file"
else
    echo "No PID file found, checking for existing processes..."
    # Try to find and kill any Python process running the ultimate_do_button_server.py
    for pid in $(ps -ef | grep "ultimate_do_button_server.py" | grep -v grep | awk '{print $2}'); do
        echo "Killing process $pid..."
        kill -9 "$pid"
    done
fi

# Apply the fix if needed
echo "Applying NextGen suggestion fix..."
python3 nextgen_overlay_suggestion_fix.py

# Start the server in the background
echo "Starting ultimate_do_button_server.py..."
python3 ultimate_do_button_server.py &

# Wait a moment for the server to start
sleep 2

# Check if the server is running
if ps -ef | grep "ultimate_do_button_server.py" | grep -v grep > /dev/null; then
    echo "✅ Ultimate DO Button server is running"
    echo "✅ Suggestions should now work correctly with the NextGen overlay"
else
    echo "❌ Failed to start Ultimate DO Button server"
    exit 1
fi

# Test the suggestion functionality
echo "Testing suggestion functionality..."
python3 test_nextgen_suggestion.py

echo "Done! The NextGen overlay should now display suggestions correctly."
