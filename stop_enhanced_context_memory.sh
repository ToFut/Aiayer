#!/bin/bash
# Stop Enhanced Context Memory System
# Gracefully stops the enhanced context memory system

echo "Stopping Enhanced Context Memory System..."

# Check for PID files
if [ -f pids/enhanced_context_memory.pid ]; then
    PID=$(cat pids/enhanced_context_memory.pid)
    if ps -p $PID > /dev/null; then
        echo "Sending SIGTERM to process $PID..."
        kill -15 $PID
        
        # Wait for graceful shutdown (max 10 seconds)
        WAIT_COUNT=0
        while ps -p $PID > /dev/null && [ $WAIT_COUNT -lt 10 ]; do
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT+1))
        done
        
        # If still running, force kill
        if ps -p $PID > /dev/null; then
            echo "Process didn't terminate gracefully, forcing..."
            kill -9 $PID
        fi
    else
        echo "Process $PID not running"
    fi
    
    # Remove PID file
    rm pids/enhanced_context_memory.pid
fi

# Check for script PID
if [ -f pids/enhanced_context_memory_script.pid ]; then
    SCRIPT_PID=$(cat pids/enhanced_context_memory_script.pid)
    if ps -p $SCRIPT_PID > /dev/null; then
        echo "Killing script process $SCRIPT_PID..."
        kill -9 $SCRIPT_PID
    fi
    
    # Remove PID file
    rm pids/enhanced_context_memory_script.pid
fi

echo "Enhanced Context Memory System stopped"