#!/bin/bash

# SensAI Enhanced Enterprise System Startup with Complete Fix
# Fixed type error and DO Button execution

echo "🚀 Starting Fixed Enhanced SensAI Enterprise System..."
echo "🎯 FIXED TYPING ERRORS + FIXED DO BUTTON EXECUTION"
echo ""

# First, fix the type error in enhanced_enterprise_backend_with_context.py
echo "🔧 Fixing type annotation in backend..."
sed -i.bak 's/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional\[str\] = None) -> List\[Dict\]:/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional[str] = None) -> List[Dict[str, Any]]:/' enhanced_enterprise_backend_with_context.py

# Verify that 'List' is imported
if ! grep -q "from typing import.*List" enhanced_enterprise_backend_with_context.py; then
    echo "🔧 Adding missing List import..."
    sed -i.bak 's/from typing import Dict, Any, Set, Optional, Tuple/from typing import Dict, Any, Set, Optional, Tuple, List/' enhanced_enterprise_backend_with_context.py
fi

# Now start the guaranteed WebSocket server for DO button
echo "🔧 Starting guaranteed WebSocket server for DO button..."

# Stop any existing servers on port 8765
echo "🛑 Stopping any existing WebSocket servers on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
sleep 2

# Create necessary directories
mkdir -p logs/websocket
mkdir -p pids

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
    cat logs/websocket/guaranteed_ws_8765.log 2>/dev/null
    exit 1
fi

# Now start the enhanced system
echo ""
echo "🚀 Starting Fixed Enhanced Enterprise System..."
./START_ENHANCED_SYSTEM.sh