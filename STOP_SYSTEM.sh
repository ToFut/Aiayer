#!/bin/bash

# SensAI Enterprise System Stop Script

echo "🛑 Stopping SensAI Enterprise System..."

# Kill all related processes
echo "📊 Stopping backend servers..."
pkill -f enterprise_backend_server_fixed
pkill -f enterprise_backend_server
pkill -f enterprise_backend
pkill -f backend_server

# Wait for processes to stop
sleep 2

# Check if any processes are still running
REMAINING=$(pgrep -f enterprise_backend)
if [ -z "$REMAINING" ]; then
    echo "✅ All SensAI processes stopped successfully!"
else
    echo "⚠️  Some processes may still be running: $REMAINING"
    echo "🔧 Force stopping remaining processes..."
    pkill -9 -f enterprise_backend
fi

echo "👋 SensAI Enterprise System stopped."
echo "🚀 To restart: ./START_SYSTEM.sh"
