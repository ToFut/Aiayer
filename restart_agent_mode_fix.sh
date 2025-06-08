#!/bin/bash

echo "🔄 Restarting enhanced enterprise backend with agent mode fix..."

# Find and kill the running process
PID=$(ps aux | grep "enhanced_enterprise_backend_with_context.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "🛑 Stopping process $PID..."
    kill $PID
    sleep 2
    # Force kill if still running
    if ps -p $PID > /dev/null; then
        echo "⚠️ Process still running, force killing..."
        kill -9 $PID
    fi
    echo "✅ Process stopped"
else
    echo "⚠️ No running process found"
fi

# Start the service with the fixed code
echo "🚀 Starting enhanced enterprise backend with fixes..."
python3 enhanced_enterprise_backend_with_context.py > logs/backend/restart_agent_mode.log 2>&1 &
NEW_PID=$!
echo "✅ Process started with PID $NEW_PID"

# Wait a moment to make sure it starts properly
sleep 3

# Check if the process is running
if ps -p $NEW_PID > /dev/null; then
    echo "✅ Enhanced enterprise backend is running with fixes!"
    echo "👀 Check logs at logs/backend/restart_agent_mode.log"
else
    echo "❌ Error starting the service. Check logs for details."
fi