#!/bin/bash
# STOP_AUTONOMOUS_SYSTEM.sh
#
# This script stops the autonomous system components gracefully,
# ensuring that all processes are properly terminated and state is saved.

echo "Stopping autonomous system..."

# Set up logging
LOG_FILE="logs/autonomous/shutdown.log"
mkdir -p logs/autonomous

echo "Starting autonomous system shutdown at $(date)" > "$LOG_FILE"

# Stop the autonomous awareness system
if [ -f "pids/autonomous_awareness.pid" ]; then
    PID=$(cat "pids/autonomous_awareness.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping autonomous awareness system (PID $PID)..." | tee -a "$LOG_FILE"
        
        # Send SIGTERM for graceful shutdown
        kill -TERM $PID
        
        # Wait for process to exit
        MAX_WAIT=10
        WAIT_COUNT=0
        while ps -p $PID > /dev/null && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
            echo "Waiting for process to exit ($WAIT_COUNT/$MAX_WAIT)..." | tee -a "$LOG_FILE"
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Process still running after $MAX_WAIT seconds, forcing termination..." | tee -a "$LOG_FILE"
            kill -9 $PID
            sleep 1
        fi
        
        # Verify process is gone
        if ! ps -p $PID > /dev/null; then
            echo "✅ Autonomous awareness system stopped successfully" | tee -a "$LOG_FILE"
        else
            echo "⚠️ Failed to stop autonomous awareness system" | tee -a "$LOG_FILE"
        fi
    else
        echo "Autonomous awareness system is not running (PID $PID not found)" | tee -a "$LOG_FILE"
    fi
    
    # Remove PID file
    rm "pids/autonomous_awareness.pid"
else
    echo "Autonomous awareness system is not running (no PID file)" | tee -a "$LOG_FILE"
fi

echo ""
echo "Do you want to stop the entire enhanced system as well? (y/n)"
read -r STOP_ALL

if [[ "$STOP_ALL" =~ ^[Yy]$ ]]; then
    echo "Stopping entire enhanced system..." | tee -a "$LOG_FILE"
    
    # Stop using existing scripts if available
    if [ -f "STOP_ENHANCED_SYSTEM.sh" ]; then
        ./STOP_ENHANCED_SYSTEM.sh | tee -a "$LOG_FILE"
    elif [ -f "stop_optimized_system.sh" ]; then
        ./stop_optimized_system.sh | tee -a "$LOG_FILE"
    else
        echo "⚠️ Could not find script to stop enhanced system" | tee -a "$LOG_FILE"
    fi
fi

echo ""
echo "Autonomous system shutdown complete at $(date)" | tee -a "$LOG_FILE"
echo "✅ All requested components have been stopped"