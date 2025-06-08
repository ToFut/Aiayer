#!/bin/bash

# Create necessary directories
mkdir -p logs
mkdir -p pids

# Check if test is already running
if [ -f pids/test_notification.pid ]; then
  PID=$(cat pids/test_notification.pid)
  if ps -p $PID > /dev/null; then
    echo "❌ Test notification system is already running (PID: $PID)"
    echo "Run ./STOP_TEST_NOTIFICATIONS.sh to stop it first"
    exit 1
  else
    # PID file exists but process is not running
    rm pids/test_notification.pid
  fi
fi

# Start the test notification loop in the background
echo "🚀 Starting test notification system..."
python3 test_fixed_notification_loop.py > logs/test_notification.log 2>&1 &

# Save the PID
echo $! > pids/test_notification.pid
echo "✅ Test notification system started (PID: $!)"
echo "Run ./STOP_TEST_NOTIFICATIONS.sh to stop it"
echo "Sending a notification every 10 seconds..."
echo "Check logs/test_notification.log for details"