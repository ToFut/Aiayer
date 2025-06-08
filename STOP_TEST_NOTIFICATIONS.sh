#!/bin/bash

# Check if PID file exists
if [ ! -f pids/test_notification.pid ]; then
  echo "❌ Test notification system is not running"
  exit 1
fi

# Get the PID
PID=$(cat pids/test_notification.pid)

# Check if process is running
if ! ps -p $PID > /dev/null; then
  echo "❌ Test notification process (PID: $PID) is not running"
  rm pids/test_notification.pid
  exit 1
fi

# Kill the process
echo "🛑 Stopping test notification system (PID: $PID)..."
kill $PID

# Wait for process to terminate
sleep 1
if ps -p $PID > /dev/null; then
  echo "Process still running, using force kill..."
  kill -9 $PID
  sleep 1
fi

# Remove PID file
rm pids/test_notification.pid
echo "✅ Test notification system stopped"