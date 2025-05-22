#!/bin/bash

# Enhanced Screen Memory System Stopper
# Stops all components of the Enhanced Screen Memory System

echo "=================================================="
echo "STOPPING ENHANCED SCREEN MEMORY SYSTEM"
echo "=================================================="

# Function to stop a service
stop_service() {
    local pid_file="$1"
    local service_name="$2"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🛑 Stopping $service_name (PID: $pid)..."
            kill -TERM "$pid"
            sleep 2
            
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚠️  Force stopping $service_name..."
                kill -KILL "$pid"
                sleep 1
            fi
            
            if ! ps -p "$pid" > /dev/null 2>&1; then
                echo "✅ $service_name stopped"
                rm -f "$pid_file"
            else
                echo "❌ Failed to stop $service_name"
            fi
        else
            echo "⚠️  $service_name PID file exists but process is not running"
            rm -f "$pid_file"
        fi
    else
        echo "📝 $service_name is not running"
    fi
}

# Stop all services
stop_service "pids/memory_service.pid" "Memory Service"
stop_service "pids/bridge_server.pid" "Enhanced Bridge Server" 
stop_service "pids/ws_server.pid" "WebSocket Server"

# Kill any remaining processes by port
echo ""
echo "🧹 Cleaning up any remaining processes..."

# Kill processes on port 8765 (WebSocket Server)
lsof -ti :8765 | xargs kill -9 2>/dev/null || true

# Kill processes on port 8766 (Bridge Server)
lsof -ti :8766 | xargs kill -9 2>/dev/null || true

echo ""
echo "✅ Enhanced Screen Memory System stopped!"
echo "=================================================="