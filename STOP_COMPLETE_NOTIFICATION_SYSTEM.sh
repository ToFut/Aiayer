#!/bin/bash
#
# STOP_COMPLETE_NOTIFICATION_SYSTEM.sh
#
# This script stops both WebSocket servers for the overlay notification system.
#

echo "========================================="
echo "Stopping Complete Notification System"
echo "========================================="
echo

# Stop the WebSocket server on port 8765
echo "Step 1: Stopping WebSocket server on port 8765..."
./stop_guaranteed_ws_8765.sh
echo

# Stop the proxy server on port 8766
echo "Step 2: Stopping proxy server on port 8766..."
./stop_fixed_do_button_proxy.sh
echo

echo "========================================="
echo "Notification System Status: STOPPED"
echo "========================================="
echo
echo "To restart the notification system:"
echo "  ./START_COMPLETE_NOTIFICATION_SYSTEM.sh"
echo
