#!/bin/bash
# start_memory_suggestion_system.sh
#
# Starts the proactive memory-aware suggestion system that:
# 1. Monitors conscious memory for suggestion triggers
# 2. Automatically pushes suggestions to the NextGen overlay
# 3. Handles transitions to Agent mode when suggestions are accepted
# 4. Executes the approved plans

# Set base directory
BASE_DIR=$(dirname "$0")
cd "$BASE_DIR" || exit 1

# Make sure logs directory exists
mkdir -p logs/memory

# Make sure memory/suggestions directory exists
mkdir -p memory/suggestions

# Make scripts executable
chmod +x memory_aware_suggestion_monitor.py

# Check if already running
if [ -f "pids/memory_suggestion_monitor.pid" ]; then
    PID=$(cat pids/memory_suggestion_monitor.pid)
    if ps -p "$PID" > /dev/null; then
        echo "Memory suggestion monitor is already running with PID: $PID"
        echo "Use stop_memory_suggestion_system.sh to stop it first"
        exit 1
    else
        echo "Stale PID file found, will start new process"
        rm -f pids/memory_suggestion_monitor.pid
    fi
fi

# Create pids directory if it doesn't exist
mkdir -p pids

# Start the memory suggestion monitor
echo "Starting memory-aware suggestion monitor..."
python3 memory_aware_suggestion_monitor.py > logs/memory/suggestion_monitor.log 2>&1 &
MONITOR_PID=$!
echo $MONITOR_PID > pids/memory_suggestion_monitor.pid
echo "Memory suggestion monitor started with PID: $MONITOR_PID"

# Display success message
echo "================================================="
echo "✅ Proactive suggestion system is now running"
echo "================================================="
echo "The system will:"
echo "- Monitor your activities through conscious memory"
echo "- Identify opportunities for automation and assistance"
echo "- Proactively push relevant suggestions to the overlay"
echo "- Transition to Agent mode when suggestions are accepted"
echo "- Execute approved automation plans"
echo ""
echo "Logs are available at: logs/memory/suggestion_monitor.log"
echo "To stop the system, run: ./stop_memory_suggestion_system.sh"
echo "================================================="

exit 0