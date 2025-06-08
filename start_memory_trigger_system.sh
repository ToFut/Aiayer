#!/bin/bash
# Start Memory Trigger System with all components

# Create necessary directories
mkdir -p logs/memory
mkdir -p pids

# Print header
echo "=========================================="
echo "  Starting Memory Trigger System"
echo "  - Using fixed_bridge_server.py on port 8768"
echo "  - EnterpriseChatWidget.svelte connects to port 8768"
echo "=========================================="

# Check if overlay/fixed_bridge_server.py is already running
if pgrep -f "python.*overlay/fixed_bridge_server.py" > /dev/null; then
    echo "✅ fixed_bridge_server.py is already running"
else
    echo "Starting fixed_bridge_server.py..."
    python overlay/fixed_bridge_server.py &
    sleep 2
    if pgrep -f "python.*overlay/fixed_bridge_server.py" > /dev/null; then
        echo "✅ fixed_bridge_server.py started successfully"
    else
        echo "❌ Failed to start fixed_bridge_server.py"
        exit 1
    fi
fi

# Start the memory trigger connector
echo "Starting updated memory trigger connector..."
python updated_connect_memory_trigger.py &
CONNECTOR_PID=$!
echo $CONNECTOR_PID > pids/memory_trigger_connector.pid

echo "=========================================="
echo "Memory Trigger System started successfully"
echo "- Use test_direct_chat_message_8768.py to test notifications"
echo "- Ensure overlay is open to see notifications"
echo "=========================================="