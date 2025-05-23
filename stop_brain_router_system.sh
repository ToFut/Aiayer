#!/bin/bash

# Stop SensAI Brain Router System

echo "🛑 STOPPING SENSAI BRAIN ROUTER SYSTEM"
echo "======================================"

# Kill processes by PID if files exist
if [ -f pids/brain_router.pid ]; then
    PID=$(cat pids/brain_router.pid)
    echo "🧠 Stopping Brain Router (PID: $PID)..."
    kill $PID 2>/dev/null
    rm pids/brain_router.pid
fi

if [ -f pids/total_screen_analyzer.pid ]; then
    PID=$(cat pids/total_screen_analyzer.pid)
    echo "👁️ Stopping Screen Analyzer (PID: $PID)..."
    kill $PID 2>/dev/null
    rm pids/total_screen_analyzer.pid
fi

if [ -f pids/process_sensor.pid ]; then
    PID=$(cat pids/process_sensor.pid)
    echo "⚙️ Stopping Process Sensor (PID: $PID)..."
    kill $PID 2>/dev/null
    rm pids/process_sensor.pid
fi

# Cleanup any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "brain_router.py" 2>/dev/null
pkill -f "total_screen_analyzer.py" 2>/dev/null
pkill -f "enhanced_fixed_process_sensor.py" 2>/dev/null

echo "✅ Brain Router System stopped successfully"
echo "🚀 To restart: ./start_brain_router_system.sh"