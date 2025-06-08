#!/bin/bash
# Restart the overlay response system

echo "🔄 Restarting the overlay response system..."

# Step 1: Kill existing overlay_response_interceptor processes
echo "📝 Stopping existing interceptor processes..."
ps aux | grep overlay_response_interceptor | grep -v grep | awk '{print $2}' | xargs -I{} kill -9 {} 2>/dev/null
sleep 1

# Step 2: Start the overlay response interceptor
echo "🚀 Starting the overlay response interceptor..."
cd "$(dirname "$0")"
python Others/overlay_response_interceptor.py > logs/overlay_response_interceptor.log 2>&1 &
sleep 2

# Step 3: Verify the interceptor is running
echo "🔍 Verifying the interceptor is running..."
if pgrep -f overlay_response_interceptor.py > /dev/null; then
    echo "✅ Overlay response interceptor is running"
else
    echo "❌ Failed to start overlay response interceptor"
    exit 1
fi

# Step 4: Restart the overlay
echo "🔄 Restarting the overlay chat window..."
./RESTART_OVERLAY.sh

echo "✅ Overlay response system restart complete!"
echo "⏱️ Please wait a few seconds for the overlay to appear"
echo "🔍 After overlay appears, try sending a test message with:"
echo "   python send_test_overlay_message.py \"Test message after restart\""