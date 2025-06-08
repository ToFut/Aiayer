#!/bin/bash
# Send suggestion to NextGen overlay
cd "$(dirname "$0")"

TITLE="${1:-NextGen Suggestion}"
MESSAGE="${2:-Would you like help with this task?}"

echo "Sending suggestion to NextGen overlay:"
echo "  Title: $TITLE"
echo "  Message: $MESSAGE"

python3 final_nextgen_suggestion.py "$TITLE" "$MESSAGE"

echo ""
echo "Usage:"
echo "  ./send_nextgen_suggestion.sh \"Title\" \"Message\""