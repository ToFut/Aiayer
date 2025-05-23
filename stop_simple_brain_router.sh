#!/bin/bash

# Stop Simple Brain Router System

echo "🛑 STOPPING SIMPLE BRAIN ROUTER SYSTEM"
echo "====================================="

# Kill server if PID file exists
if [ -f pids/simple_brain_router.pid ]; then
    PID=$(cat pids/simple_brain_router.pid)
    echo "🧠 Stopping Brain Router Server (PID: $PID)..."
    kill $PID 2>/dev/null
    rm pids/simple_brain_router.pid
fi

# Cleanup any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "simple_brain_router_server.py" 2>/dev/null

echo "✅ Simple Brain Router System stopped successfully"
echo "🚀 To restart: ./start_simple_brain_router.sh"