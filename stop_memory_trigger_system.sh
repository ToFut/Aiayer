#!/bin/bash
# Stop Memory Trigger System components

# Print header
echo "=========================================="
echo "  Stopping Memory Trigger System"
echo "=========================================="

# Stop memory trigger connector
if [ -f "pids/memory_trigger_connector.pid" ]; then
    PID=$(cat pids/memory_trigger_connector.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping memory trigger connector (PID: $PID)..."
        kill -15 $PID
        sleep 1
        if ps -p $PID > /dev/null; then
            echo "Force stopping memory trigger connector..."
            kill -9 $PID
        fi
        echo "✅ Memory trigger connector stopped"
    else
        echo "Memory trigger connector is not running"
    fi
    rm -f pids/memory_trigger_connector.pid
else
    echo "Memory trigger connector PID file not found"
fi

# Optional: Stop fixed_bridge_server.py
if pgrep -f "python.*overlay/fixed_bridge_server.py" > /dev/null; then
    echo "Do you want to stop fixed_bridge_server.py? (y/n)"
    read answer
    if [ "$answer" = "y" ]; then
        echo "Stopping fixed_bridge_server.py..."
        pkill -f "python.*overlay/fixed_bridge_server.py"
        sleep 1
        if pgrep -f "python.*overlay/fixed_bridge_server.py" > /dev/null; then
            echo "Force stopping fixed_bridge_server.py..."
            pkill -9 -f "python.*overlay/fixed_bridge_server.py"
        fi
        echo "✅ fixed_bridge_server.py stopped"
    else
        echo "Leaving fixed_bridge_server.py running"
    fi
else
    echo "fixed_bridge_server.py is not running"
fi

echo "=========================================="
echo "Memory Trigger System stopped"
echo "=========================================="