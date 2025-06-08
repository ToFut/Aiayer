#!/bin/bash
#
# START_COMPLETE_NOTIFICATION_SYSTEM.sh
#
# This script starts both WebSocket servers needed for the overlay notification system:
# 1. Port 8765 - Used by the overlay UI for doButton messages
# 2. Port 8766 - Used for the proxy server for notifications
#

echo "========================================="
echo "Starting Complete Notification System"
echo "========================================="
echo

# First, stop any existing servers
echo "Step 1: Stopping any existing WebSocket servers..."
./stop_guaranteed_ws_8765.sh
./stop_fixed_do_button_proxy.sh
echo

# Start the WebSocket server on port 8765
echo "Step 2: Starting WebSocket server on port 8765..."
python3 fixed_ws_server_8765.py > logs/ws_server_8765.log 2>&1 &
WS_PID=$!
echo $WS_PID > pids/ws_server_8765.pid
echo "WebSocket server started with PID: $WS_PID"
echo

# Start the proxy server on port 8766
echo "Step 3: Starting proxy server on port 8766..."
./start_fixed_do_button_proxy.sh
echo

# Wait a moment for servers to initialize
echo "Step 4: Waiting for servers to initialize..."
sleep 3
echo

# Test notifications to both ports
echo "Step 5: Sending test notifications..."
./send_notification_8765.sh "✅ Notification system is working on port 8765!" high true
./send_overlay_notification.sh "✅ Notification system is working on port 8766!" high true
echo

echo "========================================="
echo "Notification System Status: ACTIVE"
echo "========================================="
echo
echo "To send notifications to port 8765 (overlay doButton):"
echo "  ./send_notification_8765.sh \"Your message\" [high|medium|low] [true|false]"
echo
echo "To send notifications to port 8766 (proxy):"
echo "  ./send_notification_8766.sh \"Your message\" [high|medium|low] [true|false]"
echo "  ./send_overlay_notification.sh \"Your message\" [high|medium|low] [with-sound]"
echo
echo "To run the notification system demo:"
echo "  python3 notification_system_demo.py           # Automated demo"
echo "  python3 notification_system_demo.py --interactive  # Interactive demo"
echo
echo "To stop the notification system:"
echo "  ./STOP_COMPLETE_NOTIFICATION_SYSTEM.sh"
echo
echo "For more information, see OVERLAY_NOTIFICATION_SYSTEM_README.md"
