#!/bin/bash

# Check if a message was provided
if [ -z "$1" ]; then
  echo "Usage: ./SEND_NEXTGEN_NOTIFICATION.sh \"Your notification message\" [port] [mode]"
  echo "Example: ./SEND_NEXTGEN_NOTIFICATION.sh \"Hello from NextGen!\""
  echo "Example with port: ./SEND_NEXTGEN_NOTIFICATION.sh \"Hello!\" 8767"
  echo "Example with port and mode: ./SEND_NEXTGEN_NOTIFICATION.sh \"Hello!\" 8767 Ask"
  exit 1
fi

# Get the message and optional port and mode
MESSAGE="$1"
PORT="${2:-8767}"
MODE="${3:-Suggest}"

echo "Sending NextGen notification:"
echo "Message: $MESSAGE"
echo "Port: $PORT"
echo "Mode: $MODE"

# Run the notification script
python3 send_nextgen_notification.py "$MESSAGE" "$PORT" "$MODE"

echo ""
echo "If notification doesn't appear, try these troubleshooting steps:"
echo "1. Is the overlay running? Check with 'ps aux | grep tauri'"
echo "2. Try restarting the overlay: ./RESTART_OVERLAY.sh"
echo "3. Check wsEndpoint in app.svelte (currently set to ws://localhost:8767)"