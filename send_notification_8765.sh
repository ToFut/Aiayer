#\!/bin/bash
#
# send_notification_8765.sh
# Sends a notification to the overlay UI via port 8765 (doButton WebSocket)
#
# Usage: ./send_notification_8765.sh "Your message" [high|medium|low] [true|false]
#

# Default values
MESSAGE="$1"
IMPORTANCE="${2:-high}"
SOUND="${3:-true}"

if [ -z "$MESSAGE" ]; then
  echo "Usage: $0 \"Your notification message\" [high|medium|low] [true|false]"
  echo "Example: $0 \"New email received\" medium true"
  exit 1
fi

# Run the Python script
python3 "$(dirname "$0")/send_notification_to_port_8765.py" "$MESSAGE" "$IMPORTANCE" "$SOUND"
