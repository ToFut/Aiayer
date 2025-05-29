#!/bin/bash
# Complete System Restart with All Fixes Applied
# This script stops all components and restarts with intelligent memory feeding

echo "🔄 RESTARTING AI SYSTEM WITH ALL FIXES..."

# Kill existing processes
echo "🛑 Stopping existing processes..."
pkill -f "real_llm_backend_8767.py"
pkill -f "enhanced_fixed_process_sensor.py" 
pkill -f "total_screen_analyzer.py"
pkill -f "smart_memory_feeder.py"
sleep 2

echo "🧹 Cleaning up old logs..."
# Truncate log files to avoid clutter
> logs/backend/real_llm_8767.log
> logs/sensors/process_sensor.log
> logs/sensors/total_screen/total_screen_analyzer.log
> logs/memory/smart_feeder.log

echo "🧠 Starting Smart Memory Feeder..."
python3 smart_memory_feeder.py &
MEMORY_PID=$!
echo "Memory Feeder PID: $MEMORY_PID"
sleep 2

echo "🤖 Starting Real LLM Backend 8767..."
python3 real_llm_backend_8767.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

echo "📊 Starting Process Sensor (fixed port)..."
python3 sensors/enhanced_fixed_process_sensor.py &
PROCESS_PID=$!
echo "Process Sensor PID: $PROCESS_PID"
sleep 2

echo "🖥️ Starting Total Screen Analyzer (fixed port)..."
python3 sensors/total_screen_analyzer.py &
SCREEN_PID=$!
echo "Screen Analyzer PID: $SCREEN_PID"
sleep 2

# Save PIDs for easy cleanup
echo "💾 Saving process IDs..."
mkdir -p pids
echo $MEMORY_PID > pids/smart_memory_feeder.pid
echo $BACKEND_PID > pids/real_llm_backend_8767.pid
echo $PROCESS_PID > pids/process_sensor.pid
echo $SCREEN_PID > pids/total_screen_analyzer.pid

echo ""
echo "✅ FIXED SYSTEM STARTED SUCCESSFULLY!"
echo ""
echo "🔧 Applied Fixes:"
echo "   ✅ Fixed sensor port connections (8765 → 8767)"
echo "   ✅ Fixed LLM context truncation issue"
echo "   ✅ Added intelligent memory feeding"
echo "   ✅ Enhanced context prioritization"
echo ""
echo "🚀 Active Components:"
echo "   🧠 Smart Memory Feeder (PID: $MEMORY_PID)"
echo "   🤖 Real LLM Backend 8767 (PID: $BACKEND_PID)" 
echo "   📊 Process Sensor (PID: $PROCESS_PID)"
echo "   🖥️ Screen Analyzer (PID: $SCREEN_PID)"
echo ""
echo "📋 To test: Ask 'what apps are open?' in ASK or Suggest mode"
echo "📋 To stop: ./STOP_FIXED_SYSTEM.sh"
echo ""
echo "📊 Monitoring logs:"
echo "   Backend: tail -f logs/backend/real_llm_8767.log"
echo "   Memory:  tail -f logs/memory/smart_feeder.log"
echo "   Process: tail -f logs/sensors/process_sensor.log"