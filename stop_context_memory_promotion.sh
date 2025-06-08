#!/bin/bash
# Stop context memory promotion

PID_FILE="memory/context_promotion.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "Stopping context memory promotion with PID: $PID"
    kill $PID
    rm $PID_FILE
    echo "Context memory promotion stopped"
else
    echo "Context memory promotion PID file not found"
fi