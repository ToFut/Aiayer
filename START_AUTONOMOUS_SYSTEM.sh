#!/bin/bash
# START_AUTONOMOUS_SYSTEM.sh
#
# This script starts a comprehensive autonomous system that:
# 1. Continuously monitors user activity and system state
# 2. Proactively generates suggestions based on patterns
# 3. Executes plans when approved by the user
# 4. Stays alive and autonomous in the background
# 5. Integrates with the existing system components

# Set up environment
echo "Setting up environment for autonomous system..."

# Create necessary directories
mkdir -p logs/autonomous
mkdir -p cache/autonomous_awareness
mkdir -p pids

# Configuration
BACKEND_PORT=8767
WS_PORT=8765
MEMORY_PORT=8769
LOG_FILE="logs/autonomous/startup.log"

# Start logging
echo "Starting autonomous system setup at $(date)" > "$LOG_FILE"

# Check if system is already running
if [ -f "pids/autonomous_awareness.pid" ]; then
    PID=$(cat "pids/autonomous_awareness.pid")
    if ps -p $PID > /dev/null; then
        echo "Autonomous system is already running with PID $PID"
        echo "To restart, run STOP_AUTONOMOUS_SYSTEM.sh first"
        exit 1
    else
        echo "Removing stale PID file" | tee -a "$LOG_FILE"
        rm "pids/autonomous_awareness.pid"
    fi
fi

# Make scripts executable
chmod +x start_autonomous_awareness.sh
chmod +x stop_autonomous_awareness.sh

# Check if the required components are running
echo "Checking if required components are running..." | tee -a "$LOG_FILE"

# Check WebSocket server
WS_RUNNING=false
if [ -f "pids/ws_server_$WS_PORT.pid" ]; then
    WS_PID=$(cat "pids/ws_server_$WS_PORT.pid")
    if ps -p $WS_PID > /dev/null; then
        echo "✅ WebSocket server is running on port $WS_PORT" | tee -a "$LOG_FILE"
        WS_RUNNING=true
    else
        echo "⚠️ WebSocket server PID file exists but process is not running" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠️ WebSocket server does not appear to be running" | tee -a "$LOG_FILE"
fi

# Check backend server
BACKEND_RUNNING=false
if [ -f "pids/backend_server_$BACKEND_PORT.pid" ]; then
    BACKEND_PID=$(cat "pids/backend_server_$BACKEND_PORT.pid")
    if ps -p $BACKEND_PID > /dev/null; then
        echo "✅ Backend server is running on port $BACKEND_PORT" | tee -a "$LOG_FILE"
        BACKEND_RUNNING=true
    else
        echo "⚠️ Backend server PID file exists but process is not running" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠️ Backend server does not appear to be running" | tee -a "$LOG_FILE"
fi

# Check memory system
MEMORY_RUNNING=false
if [ -f "pids/memory_system_$MEMORY_PORT.pid" ]; then
    MEMORY_PID=$(cat "pids/memory_system_$MEMORY_PORT.pid")
    if ps -p $MEMORY_PID > /dev/null; then
        echo "✅ Memory system is running on port $MEMORY_PORT" | tee -a "$LOG_FILE"
        MEMORY_RUNNING=true
    else
        echo "⚠️ Memory system PID file exists but process is not running" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠️ Memory system does not appear to be running" | tee -a "$LOG_FILE"
fi

# Start missing components if needed
if [ "$WS_RUNNING" = false ] || [ "$BACKEND_RUNNING" = false ] || [ "$MEMORY_RUNNING" = false ]; then
    echo "Some required components are not running. Do you want to start them? (y/n)"
    read -r START_COMPONENTS
    
    if [[ "$START_COMPONENTS" =~ ^[Yy]$ ]]; then
        echo "Starting required components..." | tee -a "$LOG_FILE"
        
        # Start WebSocket server if needed
        if [ "$WS_RUNNING" = false ]; then
            echo "Starting WebSocket server..." | tee -a "$LOG_FILE"
            if [ -f "start_optimized_system.sh" ]; then
                ./start_optimized_system.sh | tee -a "$LOG_FILE"
            elif [ -f "START_ENHANCED_SYSTEM.sh" ]; then
                ./START_ENHANCED_SYSTEM.sh | tee -a "$LOG_FILE"
            else
                echo "⚠️ Could not find script to start WebSocket server" | tee -a "$LOG_FILE"
            fi
        fi
        
        # Give components time to start
        echo "Waiting for components to initialize..." | tee -a "$LOG_FILE"
        sleep 5
    else
        echo "Warning: Running autonomous system without all required components may limit functionality" | tee -a "$LOG_FILE"
    fi
fi

# Start the autonomous awareness system
echo "Starting autonomous awareness system..." | tee -a "$LOG_FILE"
python3 autonomous_awareness_integration.py > logs/autonomous/integration_stdout.log 2> logs/autonomous/integration_stderr.log &
AUTONOMOUS_PID=$!

# Save the PID
echo $AUTONOMOUS_PID > "pids/autonomous_awareness.pid"
echo "✅ Autonomous awareness system started with PID $AUTONOMOUS_PID" | tee -a "$LOG_FILE"

# Display status
echo "🚀 Autonomous system is now running!"
echo "  • Main process: PID $AUTONOMOUS_PID"
echo "  • Logs: logs/autonomous/"
echo "  • To stop: ./STOP_AUTONOMOUS_SYSTEM.sh"
echo ""
echo "The system will continuously monitor, generate suggestions,"
echo "and execute approved plans in the background."
echo ""
echo "System will stay alive until explicitly stopped."