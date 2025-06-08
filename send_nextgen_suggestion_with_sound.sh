#!/bin/bash
# send_nextgen_suggestion_with_sound.sh
# 
# A simple script to send suggestions to the NextGen overlay with proper notification handling
# 
# Usage:
#   ./send_nextgen_suggestion_with_sound.sh "Suggestion Title" "Suggestion Message"

# Check if we have enough arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 \"Suggestion Title\" \"Suggestion Message\""
    exit 1
fi

TITLE="$1"
MESSAGE="$2"

echo "Sending suggestion with notification to NextGen overlay..."
echo "Title: $TITLE"
echo "Message: $MESSAGE"

# Make sure the script is executable
chmod +x fixed_nextgen_suggestion_handler.py

# Run the Python script with the provided arguments
python3 fixed_nextgen_suggestion_handler.py "$TITLE" "$MESSAGE"

echo "Suggestion sent!"