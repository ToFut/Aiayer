#!/bin/bash
#
# Start Integrated Memory and LLM System
# This script starts all components needed for enhanced context-aware LLM responses
#

# Exit on error
set -e

# Create log and pid directories
mkdir -p logs/system
mkdir -p pids

# Stop any running components
echo "Stopping any running components..."
./stop_enhanced_context_memory.sh 2>/dev/null || true
kill $(cat pids/context_memory_server.pid 2>/dev/null) 2>/dev/null || true
kill $(cat pids/enhanced_ollama_service.pid 2>/dev/null) 2>/dev/null || true
kill $(cat pids/fixed_bridge_server.pid 2>/dev/null) 2>/dev/null || true
rm -f pids/context_memory_server.pid pids/enhanced_ollama_service.pid 2>/dev/null || true

echo "Starting integrated memory and LLM system..."

# Set up paths for Python to find modules
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 1. Start Bridge Server (handles basic communication)
echo "Starting Bridge Server..."
python fixed_bridge_server.py > logs/system/bridge_server.log 2>&1 &
echo $! > pids/bridge_server.pid
echo "Bridge Server started (PID: $(cat pids/bridge_server.pid))"
sleep 2

# 2. Start Context Memory Server (provides enhanced context)
echo "Starting Context Memory Server..."
python context_memory_server.py > logs/system/context_memory_server.log 2>&1 &
echo $! > pids/context_memory_server.pid
echo "Context Memory Server started (PID: $(cat pids/context_memory_server.pid))"
sleep 2

# 3. Start Enhanced Ollama Service (context-aware LLM responses)
echo "Starting Enhanced Ollama Service..."
python enhanced_ollama_service.py > logs/system/enhanced_ollama_service.log 2>&1 &
echo $! > pids/enhanced_ollama_service.pid
echo "Enhanced Ollama Service started (PID: $(cat pids/enhanced_ollama_service.pid))"
sleep 2

# 4. Start sensors (if needed)
echo "Starting sensors..."
# Uncomment sensor starter lines as needed
python sensors/fixed_screen_sensor.py > logs/system/screen_sensor.log 2>&1 &
echo $! > pids/screen_sensor.pid
echo "Screen Sensor started (PID: $(cat pids/screen_sensor.pid))"

python sensors/fixed_process_sensor.py > logs/system/process_sensor.log 2>&1 &
echo $! > pids/process_sensor.pid
echo "Process Sensor started (PID: $(cat pids/process_sensor.pid))"

echo "All components started successfully!"
echo "To stop the system, run: ./stop_integrated_memory_llm.sh"
echo "Check logs in logs/system/ directory"