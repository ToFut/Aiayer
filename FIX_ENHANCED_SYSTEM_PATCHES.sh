#!/bin/bash

# Patch script for enhanced system
# Applies necessary fixes before running START_ENHANCED_SYSTEM.sh

echo "🔧 Applying critical fixes before starting enhanced system..."

# 1. Fix type annotation error in enhanced_enterprise_backend_with_context.py
echo "  🔧 Fixing type annotation in backend..."
sed -i.typeerror.bak 's/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional\[str\] = None) -> List\[Dict\]:/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional[str] = None) -> List[Dict[str, Any]]:/' enhanced_enterprise_backend_with_context.py

# Verify that 'List' is imported
if ! grep -q "from typing import.*List" enhanced_enterprise_backend_with_context.py; then
    echo "  🔧 Adding missing List import..."
    sed -i.import.bak 's/from typing import Dict, Any, Set, Optional, Tuple/from typing import Dict, Any, Set, Optional, Tuple, List/' enhanced_enterprise_backend_with_context.py
fi

# 2. Prepare guaranteed WebSocket server for DO button
echo "  🔧 Preparing guaranteed WebSocket server for DO button..."

# Create necessary directories
mkdir -p logs/websocket
mkdir -p pids

# Create stop handler for guaranteed WebSocket server
echo "  🔧 Creating stop handler for guaranteed WebSocket server..."
cat > stop_guaranteed_ws_8765.sh << 'EOF'
#!/bin/bash
# Script to stop the guaranteed WebSocket server on port 8765

echo "Stopping guaranteed WebSocket server on port 8765..."

# Check if the PID file exists
if [ -f "pids/guaranteed_ws_8765.pid" ]; then
    WS_PID=$(cat pids/guaranteed_ws_8765.pid)
    
    # Check if the process is running
    if ps -p $WS_PID > /dev/null; then
        # Kill the process
        kill $WS_PID
        echo "Stopped WebSocket server (PID: $WS_PID)"
    else
        echo "WebSocket server process is not running (PID: $WS_PID)"
        # Clean up the PID file
        rm pids/guaranteed_ws_8765.pid
    fi
else
    echo "No PID file found. Stopping any WebSocket server on port 8765..."
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
fi
EOF
chmod +x stop_guaranteed_ws_8765.sh

# 3. Modify STOP_ENHANCED_SYSTEM.sh to include the WebSocket server
echo "  🔧 Creating enhanced stop script template..."
cat > STOP_ENHANCED_SYSTEM_FIXED.sh.template << 'EOF'
#!/bin/bash
echo "🛑 Stopping Complete Enhanced System (All Components)..."

# First stop the guaranteed WebSocket server
if [ -f "./stop_guaranteed_ws_8765.sh" ]; then
    echo "Stopping guaranteed WebSocket server..."
    ./stop_guaranteed_ws_8765.sh
fi

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            echo "Stopping $COMPONENT (PID: $PID)"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f real_llm_backend 2>/dev/null || true
pkill -f enhanced_brain_router 2>/dev/null || true
pkill -f contextual 2>/dev/null || true
pkill -f llm_warmup_manager 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true  
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration_service 2>/dev/null || true
pkill -f smart_memory_feeder 2>/dev/null || true
pkill -f conscious_memory 2>/dev/null || true
pkill -f semantic_search 2>/dev/null || true
pkill -f guaranteed_ws_server_8765 2>/dev/null || true

# Clean up ports
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true

echo "✅ Complete Enhanced System stopped"
echo "🔥 All components stopped including the DO button WebSocket server"
EOF
chmod +x STOP_ENHANCED_SYSTEM_FIXED.sh.template

# 4. Create guaranteed DO button start script
echo "  🔧 Creating DO button WebSocket server starter..."
cat > start_guaranteed_ws_8765.sh << 'EOF'
#!/bin/bash
# Startup script for the guaranteed WebSocket server on port 8765

# Stop any existing servers on port 8765
echo "🛑 Stopping any existing WebSocket servers on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
sleep 2

# Start the guaranteed WebSocket server
echo "🚀 Starting guaranteed WebSocket server on port 8765..."
python3 guaranteed_ws_server_8765.py > logs/websocket/guaranteed_ws_8765.log 2>&1 &
WSSERVER_PID=$!
echo $WSSERVER_PID > pids/guaranteed_ws_8765.pid

# Wait for it to start
echo "⏳ Waiting for WebSocket server to start..."
sleep 3

# Check if it's running
if ps -p $WSSERVER_PID > /dev/null; then
    echo "✅ Guaranteed WebSocket server successfully started (PID: $WSSERVER_PID)"
else
    echo "❌ WebSocket server failed to start"
    echo "Check logs: logs/websocket/guaranteed_ws_8765.log"
    exit 1
fi
EOF
chmod +x start_guaranteed_ws_8765.sh

# 5. Create post-enhanced-system startup script
echo "  🔧 Creating post-enhanced-system startup script..."
cat > start_do_button_fix.sh << 'EOF'
#!/bin/bash
# Script to start the DO button fix after the enhanced system is running

echo ""
echo "🔧 ADDING DO BUTTON EXECUTION FIX..."

# Start the guaranteed WebSocket server
./start_guaranteed_ws_8765.sh

# Replace the stop script with our enhanced version
if [ -f "STOP_ENHANCED_SYSTEM.sh" ]; then
    cp STOP_ENHANCED_SYSTEM_FIXED.sh.template STOP_ENHANCED_SYSTEM.sh
    chmod +x STOP_ENHANCED_SYSTEM.sh
    echo "✅ Enhanced stop script created"
fi

echo ""
echo "✅ DO BUTTON FIX COMPLETE!"
echo "The DO button in the overlay chat should now work correctly."
echo ""
EOF
chmod +x start_do_button_fix.sh

echo "✅ All patch scripts created successfully!"
echo ""
echo "To start the system with all fixes, run:"
echo "  1. ./START_ENHANCED_SYSTEM.sh"
echo "  2. ./start_do_button_fix.sh"
echo ""
echo "Alternatively, you can combine these commands:"
echo "  ./START_ENHANCED_SYSTEM.sh && ./start_do_button_fix.sh"
echo ""