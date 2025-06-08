#!/bin/bash
# Stop the real DO button executor

echo "Stopping real DO button executor..."

# Kill process by PID if the PID file exists
if [ -f "pids/real_do_button_executor.pid" ]; then
    pid=$(cat pids/real_do_button_executor.pid)
    if ps -p $pid > /dev/null; then
        kill -9 $pid
        echo "✅ Real DO button executor stopped (PID: $pid)"
    else
        echo "Process with PID $pid is not running"
    fi
    rm pids/real_do_button_executor.pid
else
    echo "PID file not found, trying to find process on port 8765..."
    # Alternative method: kill by port
    if lsof -ti:8765 > /dev/null; then
        lsof -ti:8765 | xargs kill -9
        echo "✅ Killed process on port 8765"
    else
        echo "No process found on port 8765"
    fi
fi

# Double-check the port is free
if lsof -ti:8765 > /dev/null; then
    echo "⚠️ Warning: Port 8765 is still in use"
else
    echo "✅ Port 8765 is now free"
fi

echo "Real DO button executor stopped successfully!"