#!/bin/bash
# Script to restart the system with fixed memory module paths

echo "Stopping any running components..."
# Kill existing Python processes
pkill -f "python3.*\.py" 2>/dev/null || true
sleep 2

echo "Fixing memory module paths..."
# Run the fix script
python3 fix_memory_module.py

echo "Starting the system with fixed configuration..."
# Run the optimized system with LLM integration
./start_optimized_system_with_llm.sh

echo "System restarted. Check the logs to verify it's working correctly:"
echo "tail -f logs/memory/memory_system.log       # Memory system logs"
echo "tail -f logs/sensors/screen_sensor/screen_sensor.log # Screen sensor logs with application detection"