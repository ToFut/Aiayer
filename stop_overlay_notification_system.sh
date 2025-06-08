#\!/bin/bash
#
# STOP_OVERLAY_NOTIFICATION_SYSTEM.sh
#
# This script stops the overlay notification system.
#

echo "========================================="
echo "Stopping Overlay Notification System"
echo "========================================="
echo

# Stop the notification proxy server
echo "Stopping notification proxy server..."
./stop_fixed_do_button_proxy.sh

echo
echo "========================================="
echo "Notification System Status: STOPPED"
echo "========================================="
echo
echo "To restart the notification system, use:"
echo "  ./START_OVERLAY_NOTIFICATION_SYSTEM.sh"
echo
