#!/bin/bash
# stop_integrated_memory_system.sh
#
# This script stops all components of the integrated memory system,
# including the LLM context connector.

# Set color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored text function
print_colored() {
    color=$1
    text=$2
    
    case $color in
        "green") echo -e "${GREEN}$text${NC}" ;;
        "yellow") echo -e "${YELLOW}$text${NC}" ;;
        "blue") echo -e "${BLUE}$text${NC}" ;;
        "red") echo -e "${RED}$text${NC}" ;;
        *) echo "$text" ;;
    esac
}

# Kill a process using its PID file
kill_pid_file() {
    pid_file=$1
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        proc_name=$(basename "$pid_file" .pid)
        
        print_colored "blue" "Stopping $proc_name (PID: $pid)..."
        
        if ps -p $pid > /dev/null; then
            # Try graceful shutdown first
            kill $pid 2>/dev/null
            
            # Give it a moment to shut down
            sleep 1
            
            # If still running, force kill
            if ps -p $pid > /dev/null; then
                print_colored "yellow" "Process $proc_name didn't shut down gracefully, forcing..."
                kill -9 $pid 2>/dev/null
            else
                print_colored "green" "✓ Process $proc_name stopped gracefully"
            fi
        else
            print_colored "yellow" "Process $proc_name was not running (PID: $pid)"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    fi
}

# Kill a process by name pattern
kill_by_pattern() {
    pattern=$1
    name=$2
    
    print_colored "blue" "Looking for $name processes..."
    pids=$(ps aux | grep -i "$pattern" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        for pid in $pids; do
            print_colored "blue" "Stopping $name (PID: $pid)..."
            
            # Try graceful shutdown first
            kill $pid 2>/dev/null
            
            # Give it a moment to shut down
            sleep 1
            
            # If still running, force kill
            if ps -p $pid > /dev/null; then
                print_colored "yellow" "Process didn't shut down gracefully, forcing..."
                kill -9 $pid 2>/dev/null
            else
                print_colored "green" "✓ Process stopped gracefully"
            fi
        done
    else
        print_colored "yellow" "No running $name processes found"
    fi
}

# Release ports if they're in use
release_port() {
    port=$1
    name=$2
    
    print_colored "blue" "Checking for processes using $name port $port..."
    
    if command -v lsof &> /dev/null; then
        pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                proc_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                print_colored "blue" "Releasing port $port from $proc_name (PID: $pid)..."
                
                # Try graceful shutdown first
                kill $pid 2>/dev/null
                
                # Give it a moment to shut down
                sleep 1
                
                # If still running, force kill
                if ps -p $pid > /dev/null; then
                    print_colored "yellow" "Process didn't release port gracefully, forcing..."
                    kill -9 $pid 2>/dev/null
                else
                    print_colored "green" "✓ Port $port released gracefully"
                fi
            done
        else
            print_colored "yellow" "No processes using port $port"
        fi
    else
        print_colored "yellow" "lsof command not available to check port usage"
    fi
}

# Main section
print_colored "blue" "Stopping Integrated Memory System..."

# Stop components using PID files
print_colored "blue" "Stopping components using PID files..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        kill_pid_file "$pid_file"
    fi
done

# Kill specific processes by pattern
print_colored "blue" "Stopping any remaining processes..."
kill_by_pattern "python3 direct_sensor_to_memory.py" "direct sensor to memory connector"
kill_by_pattern "python3 fixed_bridge_context_connector.py" "bridge context connector"
kill_by_pattern "python3 llm_context_connector.py" "LLM context connector"
kill_by_pattern "python3 sensors/enhanced_fixed_process_sensor.py" "process sensor"
kill_by_pattern "python3 sensors/enhanced_fixed_screen_sensor.py" "screen sensor"
kill_by_pattern "python3 fixed_bridge_server_enhanced.py" "bridge server"
kill_by_pattern "python3 fixed_ws_8765.py" "websocket server"
kill_by_pattern "python3 simple_ws_server_8767.py" "backend server"
kill_by_pattern "python3 monitor_context_integration.py" "context monitor"

# Release ports
print_colored "blue" "Releasing network ports..."
release_port 8765 "WebSocket/LLM"
release_port 8766 "Bridge"
release_port 8767 "Backend"
release_port 8768 "Enhanced bridge"
release_port 8769 "Memory"

# Verify all processes are stopped
print_colored "blue" "Verifying all processes are stopped..."
remaining=$(ps aux | grep -E 'direct_sensor_to_memory|fixed_bridge_context_connector|llm_context_connector|enhanced_fixed_process_sensor|enhanced_fixed_screen_sensor|fixed_bridge_server_enhanced|fixed_ws_8765|simple_ws_server_8767|monitor_context_integration' | grep -v grep)

if [ -n "$remaining" ]; then
    print_colored "yellow" "Some processes might still be running:"
    echo "$remaining" | sed 's/^/    /'
else
    print_colored "green" "✓ All processes have been stopped"
fi

# Check if ports are still in use
print_colored "blue" "Checking if ports are still in use..."
ports_in_use=false

for port in 8765 8766 8767 8768 8769; do
    if command -v lsof &> /dev/null && lsof -ti :$port &>/dev/null; then
        port_pid=$(lsof -ti :$port)
        port_proc=$(ps -p $port_pid -o comm= 2>/dev/null || echo "unknown")
        print_colored "yellow" "Port $port is still in use by $port_proc (PID: $port_pid)"
        ports_in_use=true
    fi
done

if [ "$ports_in_use" = false ]; then
    print_colored "green" "✓ All ports have been released"
fi

print_colored "green" "====================================="
print_colored "green" "✓ Integrated Memory System Stopped"
print_colored "green" "====================================="
print_colored "blue" "To restart the system, run: ./run_integrated_memory_system.sh"