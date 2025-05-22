#!/bin/bash
# update_integrated_memory_system.sh
#
# This script updates the integrated memory system to add LLM context integration,
# ensuring that context from sensors and memory is properly sent to the LLM service.

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

# Create directories if they don't exist
print_colored "blue" "Creating necessary directories..."
mkdir -p logs/llm
mkdir -p pids

# Stop any running LLM context connector
print_colored "yellow" "Stopping any existing LLM context connector..."
if [ -f "pids/llm_context_connector.pid" ]; then
    pid=$(cat "pids/llm_context_connector.pid")
    if ps -p $pid > /dev/null; then
        print_colored "yellow" "Stopping existing llm_context_connector (PID: $pid)"
        kill $pid
        sleep 1
        if ps -p $pid > /dev/null; then
            kill -9 $pid
        fi
    fi
    rm -f "pids/llm_context_connector.pid"
fi

# Also try stopping by process name
pkill -f "python3 llm_context_connector.py" 2>/dev/null || true
sleep 1

# Check if memory system is running
print_colored "blue" "Checking if memory system is running..."
memory_running=true

# Check Bridge server
if command -v lsof &> /dev/null && lsof -ti :8766 &>/dev/null; then
    print_colored "green" "✅ Bridge server is running on port 8766"
else
    print_colored "yellow" "❌ Bridge server is not running on port 8766"
    print_colored "yellow" "Start it with: ./run_integrated_memory_system.sh"
    memory_running=false
fi

# Check for process sensor
if [ -f "pids/process_sensor.pid" ]; then
    pid=$(cat "pids/process_sensor.pid")
    if ps -p $pid > /dev/null; then
        print_colored "green" "✅ Process sensor is running"
    else
        print_colored "yellow" "❌ Process sensor is not running"
        memory_running=false
    fi
else
    print_colored "yellow" "❌ Process sensor is not running (no PID file)"
    memory_running=false
fi

# Check for screen sensor
if [ -f "pids/screen_sensor.pid" ]; then
    pid=$(cat "pids/screen_sensor.pid")
    if ps -p $pid > /dev/null; then
        print_colored "green" "✅ Screen sensor is running"
    else
        print_colored "yellow" "❌ Screen sensor is not running"
        memory_running=false
    fi
else
    print_colored "yellow" "❌ Screen sensor is not running (no PID file)"
    memory_running=false
fi

# Check context file
if [ -f "memory/last_context.json" ]; then
    size=$(wc -c < "memory/last_context.json")
    if [ $size -gt 200 ]; then
        print_colored "green" "✅ Context file has data ($size bytes)"
    else
        print_colored "yellow" "❌ Context file may be empty ($size bytes)"
        memory_running=false
    fi
else
    print_colored "yellow" "❌ Context file does not exist"
    memory_running=false
fi

# Check if LLM service is available on port 8765
print_colored "blue" "Checking for LLM service on port 8765..."
if command -v lsof &> /dev/null && lsof -ti :8765 &>/dev/null; then
    print_colored "green" "✅ LLM service is running on port 8765"
    llm_running=true
else
    print_colored "yellow" "⚠️  LLM service is not detected on port 8765"
    print_colored "yellow" "The LLM context connector will still be started but may not connect"
    llm_running=false
fi

# If memory system is not running, warn the user
if [ "$memory_running" = false ]; then
    print_colored "yellow" "⚠️  Memory system appears to be incomplete or not running"
    print_colored "yellow" "Consider running ./run_integrated_memory_system.sh first"
    print_colored "blue" "Do you want to continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_colored "yellow" "Aborting update"
        exit 1
    fi
fi

# Start the LLM context connector
print_colored "blue" "Starting LLM context connector..."
python3 llm_context_connector.py > logs/llm/llm_context_connector.log 2>&1 &
pid=$!
echo $pid > pids/llm_context_connector.pid
sleep 2

# Verify the LLM context connector is running
if ps -p $pid > /dev/null; then
    print_colored "green" "✅ LLM context connector started successfully (PID: $pid)"
else
    print_colored "red" "❌ LLM context connector failed to start"
    print_colored "yellow" "Check the logs at logs/llm/llm_context_connector.log"
    exit 1
fi

# Show recent log entries
print_colored "blue" "Recent log entries from LLM context connector:"
if [ -f "logs/llm/llm_context_connector.log" ]; then
    tail -n 10 logs/llm/llm_context_connector.log
else
    print_colored "yellow" "No log file found yet"
fi

# Instructions for monitoring
print_colored "green" "==============================================="
print_colored "green" "✅ LLM context connector has been started!"
print_colored "green" "==============================================="
print_colored "yellow" "To monitor the connector:"
echo "tail -f logs/llm/llm_context_connector.log"
print_colored "yellow" "To stop the connector:"
echo "kill \$(cat pids/llm_context_connector.pid)"
print_colored "yellow" "To see if LLM context updates are being sent, check:"
echo "tail -f logs/llm/llm_context_connector.log | grep -i 'Sent context'"

# If LLM service is not detected, provide hints
if [ "$llm_running" = false ]; then
    print_colored "yellow" "⚠️  No LLM service was detected on port 8765."
    print_colored "yellow" "Make sure to start the LLM service for full functionality."
fi

print_colored "blue" "Update completed!"