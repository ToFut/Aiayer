#!/bin/bash

# Fix Neural UI DO Button Integration
echo "=== Applying Neural UI DO Button Fix ==="

# Stop relevant services
echo "Stopping DO Button services..."
pkill -f "fix_do_button_connection" 2>/dev/null || true
pkill -f "neural_ui_do_button_handler" 2>/dev/null || true
pkill -f "ultimate_do_button_server" 2>/dev/null || true

# Wait for processes to stop
sleep 2

# Create necessary directories
mkdir -p logs/do_button_fix
mkdir -p cache/plans

# Restart services
echo "Restarting DO Button services..."

# Start Ultimate DO Button Server
python3 ultimate_do_button_server.py > logs/do_button/ultimate_do_button_server.log 2>&1 &
ULTIMATE_PID=$!
echo $ULTIMATE_PID > pids/ultimate_do_button_server.pid
echo "Ultimate DO Button Server started with PID: $ULTIMATE_PID"

# Wait for server to initialize
sleep 3

# Start DO Button Connection Fix
python3 fix_do_button_connection_bridge.py > logs/do_button_fix/connection_fix.log 2>&1 &
PROXY_PID=$!
echo $PROXY_PID > pids/do_button_connection_fix.pid
echo "DO Button Connection Fix started with PID: $PROXY_PID"

# Wait for server to initialize
sleep 2

echo "✅ Fix applied! DO Button integration should now work correctly."
echo "You can verify by checking the logs:"
echo "  tail -f logs/do_button_fix/connection_fix.log"
echo "  tail -f logs/do_button/ultimate_do_button_server.log"
echo ""
echo "To test the fix, run the debug script:"
echo "  python3 debug_do_button_neural_ui.py"