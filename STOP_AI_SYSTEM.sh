#!/bin/bash

# SensAI AI-Powered Enterprise System Stop Script

echo "🛑 Stopping SensAI AI-Powered Enterprise System..."

# Kill all related processes
echo "📊 Stopping AI backend servers..."
pkill -f enterprise_backend_server_ai_powered
pkill -f enterprise_backend_server
pkill -f backend_server
pkill -f interactive_approval_client

# Wait for processes to stop
sleep 2

# Check if any processes are still running
REMAINING=$(pgrep -f enterprise_backend)
if [ -z "$REMAINING" ]; then
    echo "✅ All SensAI AI processes stopped successfully!"
else
    echo "⚠️  Some processes may still be running: $REMAINING"
    echo "🔧 Force stopping remaining processes..."
    pkill -9 -f enterprise_backend
fi

echo "👋 SensAI AI-Powered Enterprise System stopped."
echo "🚀 To restart: ./START_AI_SYSTEM.sh"
echo "🧪 To run interactive client: python3 interactive_approval_client.py"
