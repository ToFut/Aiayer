#\!/bin/bash
#
# START_OVERLAY_NOTIFICATION_SYSTEM.sh
#
# This script starts the overlay notification system and sends a test notification
# to verify everything is working correctly.
#

echo "========================================="
echo "Starting Overlay Notification System"
echo "========================================="
echo

# First, stop any existing proxy server
echo "Step 1: Stopping any existing proxy server..."
./stop_fixed_do_button_proxy.sh

# Start the proxy server
echo
echo "Step 2: Starting the notification proxy server..."
./start_fixed_do_button_proxy.sh

# Wait a moment for the server to initialize
echo
echo "Step 3: Waiting for server initialization..."
sleep 3

# Send a test notification
echo
echo "Step 4: Sending test notification..."
./send_overlay_notification.sh "✅ Notification system is active and working\!" high with-sound

echo
echo "========================================="
echo "Notification System Status: ACTIVE"
echo "========================================="
echo
echo "To send notifications, use:"
echo "  ./send_overlay_notification.sh \"Your message\" [high|medium|low] [with-sound]"
echo
echo "To stop the notification system, use:"
echo "  ./stop_fixed_do_button_proxy.sh"
echo
echo "For more information, see OVERLAY_NOTIFICATION_SYSTEM_README.md"
