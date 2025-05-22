#!/bin/bash

# Enhanced Screen Memory System Launcher
# Starts the complete system with Total Screen Analyzer and Enhanced Memory Processing

echo "=================================================="
echo "ENHANCED SCREEN MEMORY SYSTEM LAUNCHER"
echo "=================================================="

# Function to check if a process is running
check_process() {
    local pid_file="$1"
    local process_name="$2"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ $process_name is running (PID: $pid)"
            return 0
        else
            echo "⚠️  $process_name PID file exists but process is not running"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo "❌ $process_name is not running"
        return 1
    fi
}

# Function to start a service
start_service() {
    local script="$1"
    local service_name="$2"
    local pid_file="$3"
    
    echo "🚀 Starting $service_name..."
    
    if [ -f "$script" ]; then
        python3 "$script" &
        local pid=$!
        echo "$pid" > "$pid_file"
        sleep 2
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ $service_name started successfully (PID: $pid)"
            return 0
        else
            echo "❌ Failed to start $service_name"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo "❌ Script not found: $script"
        return 1
    fi
}

# Create necessary directories
mkdir -p logs/bridge
mkdir -p logs/memory
mkdir -p pids

# Check current status
echo "📊 Checking current system status..."
check_process "pids/bridge_server.pid" "Enhanced Bridge Server"
check_process "pids/memory_service.pid" "Memory Service"
check_process "pids/ws_server.pid" "WebSocket Server"

echo ""
echo "🔧 Starting Enhanced Screen Memory System..."
echo ""

# Start WebSocket Server (main server)
if ! check_process "pids/ws_server.pid" "WebSocket Server"; then
    if start_service "bridge_server.py" "WebSocket Server" "pids/ws_server.pid"; then
        echo "✅ WebSocket Server started"
    else
        echo "❌ Failed to start WebSocket Server"
        exit 1
    fi
fi

# Start Enhanced Bridge Server
if ! check_process "pids/bridge_server.pid" "Enhanced Bridge Server"; then
    if start_service "fixed_bridge_server_enhanced.py" "Enhanced Bridge Server" "pids/bridge_server.pid"; then
        echo "✅ Enhanced Bridge Server started"
    else
        echo "❌ Failed to start Enhanced Bridge Server"
        exit 1
    fi
fi

# Start Memory Service
if ! check_process "pids/memory_service.pid" "Memory Service"; then
    if start_service "memory/memory_service.py" "Memory Service" "pids/memory_service.pid"; then
        echo "✅ Memory Service started"
    else
        echo "❌ Failed to start Memory Service"
        exit 1
    fi
fi

echo ""
echo "🎉 Enhanced Screen Memory System is now running!"
echo ""
echo "📋 System Components:"
echo "   • WebSocket Server (port 8765) - Main communication hub"
echo "   • Enhanced Bridge Server (port 8766) - Processes Total Screen Analyzer data"
echo "   • Memory Service - Stores rich analysis in memory layers"
echo ""
echo "🔍 To test the system:"
echo "   python3 test_total_screen_memory_flow.py"
echo ""
echo "📊 To monitor the system:"
echo "   tail -f logs/bridge/bridge_server.log"
echo "   tail -f logs/memory/memory_service.log"
echo ""
echo "🛑 To stop the system:"
echo "   ./stop_enhanced_screen_memory_system.sh"
echo ""
echo "=================================================="
echo "System ready! Rich screen analysis will now be properly stored in memory."
echo "=================================================="