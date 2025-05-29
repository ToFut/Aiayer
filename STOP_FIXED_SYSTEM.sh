#!/bin/bash
# Stop Fixed AI System

echo "🛑 Stopping Fixed AI System..."

# Read and kill PIDs
if [ -f "pids/smart_memory_feeder.pid" ]; then
    PID=$(cat pids/smart_memory_feeder.pid)
    echo "Stopping Smart Memory Feeder (PID: $PID)..."
    kill $PID 2>/dev/null
fi

if [ -f "pids/real_llm_backend_8767.pid" ]; then
    PID=$(cat pids/real_llm_backend_8767.pid)
    echo "Stopping Real LLM Backend (PID: $PID)..."
    kill $PID 2>/dev/null
fi

if [ -f "pids/process_sensor.pid" ]; then
    PID=$(cat pids/process_sensor.pid)
    echo "Stopping Process Sensor (PID: $PID)..."
    kill $PID 2>/dev/null
fi

if [ -f "pids/total_screen_analyzer.pid" ]; then
    PID=$(cat pids/total_screen_analyzer.pid)
    echo "Stopping Screen Analyzer (PID: $PID)..."
    kill $PID 2>/dev/null
fi

# Force kill any remaining processes
echo "Force killing any remaining processes..."
pkill -f "real_llm_backend_8767.py"
pkill -f "enhanced_fixed_process_sensor.py" 
pkill -f "total_screen_analyzer.py"
pkill -f "smart_memory_feeder.py"

# Clean up PID files
rm -f pids/*.pid

echo "✅ Fixed AI System stopped successfully!"