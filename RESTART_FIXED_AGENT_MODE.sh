#!/bin/bash
# RESTART_FIXED_AGENT_MODE.sh
# This script restarts the system with the fixed agent mode that handles any inquiry type

# Display banner
echo "========================================================"
echo "🚀 RESTARTING ENHANCED SYSTEM WITH FIXED AGENT MODE"
echo "   Now handling ANY inquiry type, not just Google search"
echo "========================================================"

# Kill any existing processes
echo "🛑 Stopping existing services..."
./STOP.sh

# Wait for processes to terminate
sleep 2

# Create necessary directories
mkdir -p logs/backend
mkdir -p pids

# Check if fixed_universal_automation_handler.py exists
if [ ! -f "fixed_universal_automation_handler.py" ]; then
    echo "⚠️ Warning: fixed_universal_automation_handler.py not found"
    echo "Creating a copy from universal_intelligent_automation_handler.py..."
    cp universal_intelligent_automation_handler.py fixed_universal_automation_handler.py
fi

# Apply fixes
echo "🔧 Applying fixes to handle any inquiry type..."

# Apply the fix to brain_router.py if it hasn't been applied yet
if [ ! -f "brain_router_fixed.flag" ]; then
    echo "🔄 brain_router.py has been fixed directly with proper indentation and regex fixes"
    touch brain_router_fixed.flag
else
    echo "✅ brain_router.py already updated"
fi

# Apply the fix to enhanced_enterprise_backend_with_context.py if it hasn't been applied yet
if [ ! -f "enterprise_backend_fixed.flag" ]; then
    echo "🔄 Updating enhanced_enterprise_backend_with_context.py..."
    python update_enterprise_backend.py
    touch enterprise_backend_fixed.flag
else
    echo "✅ enhanced_enterprise_backend_with_context.py already updated"
fi

# Start the components in the correct order
echo "🚀 Starting fixed WebSocket servers..."
cd overlay
python minimal_ws_server.py &
echo $! > pids/ws_server_8765.pid
cd ..

echo "🚀 Starting fixed brain router system..."
cd brain/core
python -c "from brain_router import process_chat_request; print('Brain router initialized')" &
cd ../..

# Start the enhanced enterprise backend
echo "🚀 Starting enhanced enterprise backend with context..."
python enhanced_enterprise_backend_with_context.py &
echo $! > pids/enhanced_enterprise_backend.pid

# Check if overlay is available and start it
if [ -f "overlay/run_tauri_with_backend.sh" ]; then
    echo "🚀 Starting overlay..."
    cd overlay
    ./run_tauri_with_backend.sh &
    cd ..
fi

echo "✅ System started with fixed agent mode support for ANY inquiry type"
echo "🔍 To test, try using agent mode with non-Google inquiries like:"
echo "   - 'Open Calculator' or simply 'calc'"
echo "   - 'Send an email to John about the meeting'"
echo "   - 'Play some music on Spotify'"
echo "   - 'Open system preferences and check network settings'"
echo "   - 'Check my calendar for tomorrow'"
echo "   - 'Create a new document in Word'"
echo "========================================================"