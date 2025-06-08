#!/bin/bash
# Start the fixed real DO button executor that properly connects LLM plans to execution

# Stop any existing servers on port 8765
echo "Stopping any existing WebSocket servers on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true

# Make sure the logs directory exists
mkdir -p logs/websocket

# Start the real DO button executor
echo "Starting fixed real DO button executor on port 8765..."
nohup python3 real_do_button_executor_fixed.py > logs/websocket/real_do_button_executor_fixed_stdout.log 2>&1 &

# Save PID
echo $! > pids/real_do_button_executor.pid

# Wait for the server to start
sleep 2

# Check if the server is running
if lsof -ti:8765 > /dev/null; then
    echo "✅ Fixed real DO button executor is running on port 8765"
    echo "✅ This server will properly load and execute LLM-generated plans step by step"
    echo "✅ Log file: logs/websocket/real_do_button_executor.log"
else
    echo "❌ Failed to start fixed real DO button executor"
    echo "Check logs/websocket/real_do_button_executor_fixed_stdout.log for errors"
    exit 1
fi

echo "Fixed real DO button executor started successfully!"