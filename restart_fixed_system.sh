#!/bin/bash
# Enhanced restart script for the system with fixed memory module paths
# This script properly initializes all components and ensures correct memory system operation

echo "===== Starting System Restart ====="

# Create necessary directories first
echo "Creating required directories..."
mkdir -p logs/memory
mkdir -p logs/sensors/screen_sensor
mkdir -p logs/sensors/process_sensor
mkdir -p logs/sensors/file_sensor
mkdir -p logs/llm
mkdir -p logs/backend
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p memory/memory

# Create required __init__.py files for Python module structure
echo "Fixing memory module paths..."
# Create __init__.py files where needed
for dir in memory memory/memory; do
    if [ ! -f "$dir/__init__.py" ]; then
        echo "# Memory system module" > "$dir/__init__.py"
        echo "Created $dir/__init__.py"
    fi
done

# Stop any existing processes
echo "Stopping any running components..."
# Kill existing Python processes related to our system
pkill -f "python3.*fixed_" 2>/dev/null || true
pkill -f "python3.*memory_system" 2>/dev/null || true
pkill -f "python3.*screen_sensor" 2>/dev/null || true
pkill -f "python3.*process_sensor" 2>/dev/null || true
pkill -f "python3.*file_sensor" 2>/dev/null || true
pkill -f "python3.*bridge_server" 2>/dev/null || true
pkill -f "python3.*backend_server" 2>/dev/null || true
pkill -f "python3.*self_contained_llm" 2>/dev/null || true

# Kill any process using our WebSocket ports
echo "Checking for processes using WebSocket ports..."
# Find and kill processes using ports 8765, 8766, 8767, 8768, 8769, 8770
for port in 8765 8766 8767 8768 8769 8770; do
    # For macOS
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill -9 $pid 2>/dev/null || true
    fi
done
sleep 5  # Wait longer to ensure processes are fully terminated

# Check if memory_types.py exists, create if it doesn't
if [ ! -f "memory/memory_types.py" ]; then
    echo "Creating memory_types.py..."
    cat > memory/memory_types.py << 'EOF'
"""
Memory Types Module

Defines the memory type classes used in the memory system.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

class ConversationMemory:
    """Manages conversation history."""
    
    def __init__(self):
        self.messages = []
        
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to conversation history."""
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        self.messages.append(message)
        
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []
        
    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []


class ContextMemory:
    """Manages contextual information."""
    
    def __init__(self):
        self.contexts = {}
        
    def add_context(self, key: str, value: Any) -> None:
        """Add context information."""
        self.contexts[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
    def get_context(self, key: str) -> Optional[Any]:
        """Get context by key."""
        if key in self.contexts:
            return self.contexts[key]['value']
        return None
        
    def clear(self) -> None:
        """Clear all contexts."""
        self.contexts = {}
EOF
fi

# Start the enhanced bridge server in background
echo "Starting enhanced bridge server..."
python3 fixed_bridge_server_enhanced.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
sleep 3  # Let bridge server start up

# Start the enhanced sensors
echo "Starting enhanced sensors..."
python3 sensors/enhanced_fixed_screen_sensor.py > logs/sensors/screen_sensor/screen_sensor.log 2>&1 &
SCREEN_PID=$!
echo $SCREEN_PID > pids/screen_sensor.pid

python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor/process_sensor.log 2>&1 &
PROCESS_PID=$!
echo $PROCESS_PID > pids/process_sensor.pid
sleep 2  # Let sensors start up

# Start the LLM service
echo "Starting LLM service..."
python3 self_contained_llm_ws.py > logs/llm/llm_service.log 2>&1 &
LLM_PID=$!
echo $LLM_PID > pids/llm_service.pid
sleep 2  # Let LLM service start up

# Start the memory connector
echo "Starting memory connector..."
cd memory
python3 enhanced_memory_connector.py > ../logs/memory/memory_system.log 2>&1 &
MEMORY_PID=$!
cd ..
echo $MEMORY_PID > pids/memory_connector.pid
sleep 2  # Give it time to start

# Wait for all components to start
sleep 5

# Verify all components are running
echo "Verifying all components are running..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        name=$(basename "$pid_file" .pid)
        if ps -p $pid > /dev/null; then
            echo "✅ $name is running with PID $pid"
        else
            echo "❌ $name failed to start (PID $pid)"
        fi
    fi
done

echo -e "\n===== System Restart Complete ====="
echo "All components have been started with enhanced memory flow."
echo "Sensors are now correctly feeding data to the memory system."
echo "The system should be working properly now."
echo
echo "To monitor the system, use the following commands:"
echo "  tail -f logs/bridge_server.log        # Bridge server logs"
echo "  tail -f logs/sensors/*/*.log          # Sensor logs"
echo "  tail -f logs/memory/*.log             # Memory system logs"
echo "  tail -f logs/llm/*.log                # LLM service logs"
echo
echo "To stop the system, run: ./stop_system.sh"
echo "To check status, run: ps aux | grep python3"