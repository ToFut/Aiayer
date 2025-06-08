#!/bin/bash

echo "🔄 Restarting the Overlay with FIXED WebSocket Configuration..."

# Find all overlay processes
OVERLAY_PIDS=$(ps aux | grep "ai-assistant-overlay" | grep -v grep | awk '{print $2}')

# Find npm/node processes related to overlay
NPM_PIDS=$(ps aux | grep -E "node.*vite|tauri dev" | grep -v grep | awk '{print $2}')

# Kill any existing overlay processes
if [ -n "$OVERLAY_PIDS" ]; then
    echo "📝 Stopping existing overlay processes: $OVERLAY_PIDS"
    kill -9 $OVERLAY_PIDS 2>/dev/null || true
else
    echo "📝 No existing overlay processes found"
fi

# Kill any npm/node processes related to overlay
if [ -n "$NPM_PIDS" ]; then
    echo "📝 Stopping npm/node processes: $NPM_PIDS"
    kill -9 $NPM_PIDS 2>/dev/null || true
fi

# Wait for processes to terminate
sleep 2

# Start the overlay
echo "🚀 Starting the overlay with FIXED configuration..."
echo "🔌 WebSocket connections updated to use port 8767 instead of 8766"
cd overlay && ./run_tauri_with_backend.sh &

echo "✅ Overlay restart command sent"
echo "⏱️ Please wait a few seconds for the overlay to appear"
echo "🔍 To test the overlay, you can:"
echo "   1. Ask a question in the chat when overlay appears"
echo "   2. Send a test notification: ./SEND_NOTIFICATION.sh \"Test notification\""
echo "   3. Check backend logs: tail -f logs/backend/real_llm_8767.log"
echo ""
echo "💡 If you still don't see responses, run ./RESTART_FIXED_SYSTEM.sh to restart the backend"