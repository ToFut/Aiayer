#!/bin/bash
# send_overlay_notification.sh
# Script to send notifications to the overlay UI
# Usage: ./send_overlay_notification.sh "Your notification message" [high|medium|low] [with-sound]

# Default values
MESSAGE="$1"
IMPORTANCE="${2:-high}"
SOUND="${3:-no-sound}"

if [ -z "$MESSAGE" ]; then
  echo "Usage: $0 \"Your notification message\" [high|medium|low] [with-sound]"
  echo "Example: $0 \"New email received\" medium with-sound"
  exit 1
fi

# Check importance
if [ "$IMPORTANCE" != "high" ] && [ "$IMPORTANCE" != "medium" ] && [ "$IMPORTANCE" != "low" ]; then
  echo "Invalid importance: $IMPORTANCE"
  echo "Valid values: high, medium, low"
  echo "Using default: high"
  IMPORTANCE="high"
fi

# Check if sound should be played
SOUND_FLAG=""
if [ "$SOUND" == "with-sound" ]; then
  SOUND_FLAG="--sound"
fi

echo "Sending notification: $MESSAGE"
echo "Importance: $IMPORTANCE"
echo "Sound: ${SOUND_FLAG:-No sound}"
echo ""

# Run the notification script
python3 "$(dirname "$0")/fixed_notification_test.py" "$MESSAGE" --importance "$IMPORTANCE" $SOUND_FLAG

# Exit with the same status code as the Python script
exit $?