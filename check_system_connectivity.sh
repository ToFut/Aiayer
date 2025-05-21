#!/bin/bash
# Script to check the connectivity of all system components
# This verifies that the WebSocket servers are running and accessible

echo "===== System Connectivity Check ====="
echo "Checking all WebSocket connections..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check bridge server (port 8768)
echo -n "Checking bridge server (port 8768): "
nc -z localhost 8768 &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Available"
else
    echo "❌ Not available"
fi

# Check LLM service (port 8770)
echo -n "Checking LLM service (port 8770): "
nc -z localhost 8770 &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Available"
else
    echo "❌ Not available"
fi

# Run connection test script for more detailed checks
echo -e "\nRunning WebSocket connection tests..."
python3 test_ws_connections.py

# Check if specific processes are running
echo -e "\nChecking system processes..."

check_process() {
    process_name=$1
    pid_file="pids/$process_name.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "✅ $process_name is running with PID $pid"
            return 0
        else
            echo "❌ $process_name is not running (PID $pid is invalid)"
            return 1
        fi
    else
        echo "❌ $process_name PID file not found"
        return 1
    fi
}

# Check each component
check_process "bridge_server"
check_process "llm_service"
check_process "screen_sensor"
check_process "process_sensor"
check_process "memory_connector"

echo -e "\n===== Connectivity Check Complete ====="
echo "If any components are not running, restart the system with:"
echo "  ./restart_fixed_system.sh"