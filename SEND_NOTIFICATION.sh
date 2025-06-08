#!/bin/bash

# Check if a message was provided
if [ -z "$1" ]; then
  echo "Usage: ./SEND_NOTIFICATION.sh \"Your notification message\" [port] [mode]"
  echo "Example: ./SEND_NOTIFICATION.sh \"Hello from the notification system!\""
  echo "Example with port: ./SEND_NOTIFICATION.sh \"Hello!\" 8768"
  echo "Example with port and mode: ./SEND_NOTIFICATION.sh \"Hello!\" 8768 Ask"
  exit 1
fi

# Get the message and optional port and mode
MESSAGE="$1"
PORT="${2:-8768}"
MODE="${3:-Suggest}"

echo "Sending notification:"
echo "Message: $MESSAGE"
echo "Port: $PORT"
echo "Mode: $MODE"

# Run the notification script
python3 send_simple_notification.py "$MESSAGE" "$PORT" "$MODE"