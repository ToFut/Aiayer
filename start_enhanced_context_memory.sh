#!/bin/bash
# Start Enhanced Context Memory System
# Starts the enhanced context memory system with LLaVA visual analysis

# Make script executable
chmod +x run_enhanced_context_memory.py

# Set up environment (assuming venv is already activated)
echo "Starting Enhanced Context Memory System with LLaVA Visual Analysis"

# Create logs directory
mkdir -p logs/system

# Start the system in the background
python3 run_enhanced_context_memory.py > logs/system/enhanced_context_memory_stdout.log 2>&1 &

# Save PID for later termination
echo $! > pids/enhanced_context_memory_script.pid

echo "Enhanced Context Memory System started (PID: $!)"
echo "Logs available at logs/system/enhanced_context_memory.log"
echo "To stop, run: ./stop_enhanced_context_memory.sh"