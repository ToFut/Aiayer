#!/bin/bash
# send_notification_8766.sh
# Script to send notifications directly to port 8766
# Usage: ./send_notification_8766.sh "Your notification message" [high|medium|low] [true|false]

# Default values
MESSAGE="$1"
IMPORTANCE="${2:-high}"
SOUND="${3:-true}"

# Run the Python script
python3 "$(dirname "$0")/send_notification_to_port_8766.py" "$MESSAGE" "$IMPORTANCE" "$SOUND"

# Exit with the same status code as the Python script
exit $?