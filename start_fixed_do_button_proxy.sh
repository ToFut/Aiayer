#!/bin/bash
#
# Start Fixed DO Button Proxy
#
# This script starts the fixed minimal DO button proxy that ensures
# plans exist before execution.
#

echo "Starting Fixed DO Button Proxy..."

# Create required directories
mkdir -p logs/do_button_fix
mkdir -p pids
mkdir -p cache/plans

# Kill any existing proxy
if lsof -ti:8766 >/dev/null; then
  echo "Stopping existing DO Button Fix Proxy on port 8766..."
  lsof -ti:8766 | xargs kill -9
  sleep 2
fi

if [ -f pids/do_button_proxy.pid ]; then
    echo "Stopping existing proxy by PID..."
    pid=$(cat pids/do_button_proxy.pid)
    if ps -p $pid > /dev/null; then
        kill $pid
        sleep 1
    fi
    rm pids/do_button_proxy.pid
fi

# Make script executable
chmod +x fixed_minimal_do_button_proxy.py

# Start the proxy
echo "Starting fixed minimal DO button proxy..."
python3 fixed_minimal_do_button_proxy.py > logs/do_button_fix/proxy_output.log 2>&1 &

# Store PID
echo $! > pids/do_button_proxy.pid
echo "Proxy started with PID: $(cat pids/do_button_proxy.pid)"

# Wait a moment
sleep 2

# Check if it's running
if ps -p $(cat pids/do_button_proxy.pid) > /dev/null; then
    echo "✅ Fixed DO Button Proxy is running"
    
    # Verify WebSocket is listening
    if lsof -i :8766 | grep LISTEN; then
        echo "✅ WebSocket server is listening on port 8766"
    else
        echo "❌ WebSocket server is not listening on port 8766!"
        echo "Check logs/do_button_fix/proxy_output.log for errors"
        tail -n 20 logs/do_button_fix/proxy_output.log
    fi
else
    echo "❌ Proxy failed to start! Check logs/do_button_fix/proxy_output.log"
    tail -n 20 logs/do_button_fix/proxy_output.log
fi

echo "Done."