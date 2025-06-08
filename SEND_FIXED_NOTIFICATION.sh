#!/bin/bash

# Make the script executable
chmod +x fixed_nextgen_notification.py

# Check if a message was provided
if [ -z "$1" ]; then
  echo "Usage: ./SEND_FIXED_NOTIFICATION.sh \"Your notification message\" [port] [mode]"
  echo "Example: ./SEND_FIXED_NOTIFICATION.sh \"Hello from the notification system!\""
  echo "Example with port: ./SEND_FIXED_NOTIFICATION.sh \"Hello!\" 8768"
  echo "Example with port and mode: ./SEND_FIXED_NOTIFICATION.sh \"Hello!\" 8768 Ask"
  exit 1
fi

# Get the message
MESSAGE="$1"

# Get the port if provided, otherwise use default
if [ -n "$2" ]; then
  PORT="--port $2"
else
  PORT=""
fi

# Get the mode if provided, otherwise use default
if [ -n "$3" ]; then
  MODE="--mode $3"
else
  MODE="--mode Suggest"
fi

# Run the notification script
echo "Sending notification: \"$MESSAGE\""
python3 fixed_nextgen_notification.py "$MESSAGE" $PORT $MODE

echo "✅ Notification sent! Check the overlay to see if it appears."