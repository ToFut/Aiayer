#!/bin/bash
# check_context_integration.sh
# Script to check the status of the context integration system

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored text
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

# Check if all services are running
check_services() {
    print_colored "blue" "Checking context integration services..."
    
    # Check bridge server
    if lsof -ti :8766 &>/dev/null; then
        print_colored "green" "✅ Bridge server is running (port 8766)"
    else
        print_colored "red" "❌ Bridge server is NOT running (port 8766)"
    fi
    
    # Check WebSocket server
    if lsof -ti :8765 &>/dev/null; then
        print_colored "green" "✅ WebSocket server is running (port 8765)"
    else
        print_colored "red" "❌ WebSocket server is NOT running (port 8765)"
    fi
    
    # Check backend server
    if lsof -ti :8767 &>/dev/null; then
        print_colored "green" "✅ Backend server is running (port 8767)"
    else
        print_colored "red" "❌ Backend server is NOT running (port 8767)"
    fi
    
    # Check running processes
    print_colored "blue" "Checking process status..."
    
    # Process sensor
    if [ -f "pids/process_sensor.pid" ]; then
        pid=$(cat "pids/process_sensor.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ Process sensor is running (PID: $pid)"
        else
            print_colored "red" "❌ Process sensor is NOT running (PID file exists but process is gone)"
        fi
    else
        print_colored "red" "❌ Process sensor PID file not found"
    fi
    
    # Screen sensor
    if [ -f "pids/screen_sensor.pid" ]; then
        pid=$(cat "pids/screen_sensor.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ Screen sensor is running (PID: $pid)"
        else
            print_colored "red" "❌ Screen sensor is NOT running (PID file exists but process is gone)"
        fi
    else
        print_colored "red" "❌ Screen sensor PID file not found"
    fi
    
    # Direct sensor-memory integration
    if [ -f "pids/direct_sensor_memory.pid" ]; then
        pid=$(cat "pids/direct_sensor_memory.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ Direct sensor-memory integration is running (PID: $pid)"
        else
            print_colored "red" "❌ Direct sensor-memory integration is NOT running (PID file exists but process is gone)"
        fi
    else
        print_colored "red" "❌ Direct sensor-memory integration PID file not found"
    fi
    
    # Context monitor
    if [ -f "pids/context_monitor.pid" ]; then
        pid=$(cat "pids/context_monitor.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ Context integration monitor is running (PID: $pid)"
        else
            print_colored "red" "❌ Context integration monitor is NOT running (PID file exists but process is gone)"
        fi
    else
        print_colored "red" "❌ Context integration monitor PID file not found"
    fi
    
    # LLM context connector
    if [ -f "pids/llm_context_connector.pid" ]; then
        pid=$(cat "pids/llm_context_connector.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ LLM context connector is running (PID: $pid)"
        else
            print_colored "red" "❌ LLM context connector is NOT running (PID file exists but process is gone)"
        fi
    else
        print_colored "yellow" "⚠️ LLM context connector PID file not found (run update_integrated_memory_system.sh to add LLM connectivity)"
    fi
}

# Check memory files
check_memory_files() {
    print_colored "blue" "Checking memory files..."
    
    # Check memory state file
    if [ -f "memory/memory_state.json" ]; then
        size=$(wc -c < "memory/memory_state.json")
        mod_time=$(stat -f "%m" "memory/memory_state.json")
        current_time=$(date +%s)
        age=$((current_time - mod_time))
        
        if [ $size -gt 200 ]; then
            print_colored "green" "✅ Memory state file exists and has data ($size bytes)"
        else
            print_colored "red" "❌ Memory state file exists but may be empty ($size bytes)"
        fi
        
        if [ $age -lt 300 ]; then
            print_colored "green" "✅ Memory state file was updated recently ($age seconds ago)"
        else
            print_colored "yellow" "⚠️ Memory state file is stale ($age seconds since last update)"
        fi
    else
        print_colored "red" "❌ Memory state file does not exist"
    fi
    
    # Check context file
    if [ -f "memory/last_context.json" ]; then
        size=$(wc -c < "memory/last_context.json")
        mod_time=$(stat -f "%m" "memory/last_context.json")
        current_time=$(date +%s)
        age=$((current_time - mod_time))
        
        if [ $size -gt 200 ]; then
            print_colored "green" "✅ Context file exists and has data ($size bytes)"
        else
            print_colored "red" "❌ Context file exists but may be empty ($size bytes)"
        fi
        
        if [ $age -lt 300 ]; then
            print_colored "green" "✅ Context file was updated recently ($age seconds ago)"
        else
            print_colored "yellow" "⚠️ Context file is stale ($age seconds since last update)"
        fi
        
        # Display some context info
        print_colored "blue" "Context file content:"
        cat "memory/last_context.json" | grep -E "active_window|active_app|timestamp" | sed 's/^/    /'
    else
        print_colored "red" "❌ Context file does not exist"
    fi
}

# Check sensor data files
check_sensor_files() {
    print_colored "blue" "Checking sensor cache files..."
    
    # Check process cache
    if [ -f "cache/process_sensor/process_cache.json" ]; then
        size=$(wc -c < "cache/process_sensor/process_cache.json")
        mod_time=$(stat -f "%m" "cache/process_sensor/process_cache.json")
        current_time=$(date +%s)
        age=$((current_time - mod_time))
        
        if [ $size -gt 100 ]; then
            print_colored "green" "✅ Process cache file exists and has data ($size bytes)"
        else
            print_colored "red" "❌ Process cache file exists but may be empty ($size bytes)"
        fi
        
        if [ $age -lt 120 ]; then
            print_colored "green" "✅ Process cache file was updated recently ($age seconds ago)"
        else
            print_colored "yellow" "⚠️ Process cache file is stale ($age seconds since last update)"
        fi
    else
        print_colored "red" "❌ Process cache file does not exist"
    fi
    
    # Check screen cache
    if [ -f "cache/screen_sensor/last_screen.json" ]; then
        size=$(wc -c < "cache/screen_sensor/last_screen.json")
        mod_time=$(stat -f "%m" "cache/screen_sensor/last_screen.json")
        current_time=$(date +%s)
        age=$((current_time - mod_time))
        
        if [ $size -gt 100 ]; then
            print_colored "green" "✅ Screen cache file exists and has data ($size bytes)"
        else
            print_colored "red" "❌ Screen cache file exists but may be empty ($size bytes)"
        fi
        
        if [ $age -lt 120 ]; then
            print_colored "green" "✅ Screen cache file was updated recently ($age seconds ago)"
        else
            print_colored "yellow" "⚠️ Screen cache file is stale ($age seconds since last update)"
        fi
    else
        print_colored "red" "❌ Screen cache file does not exist"
    fi
}

# Check data flow from sensors to memory
check_data_flow() {
    print_colored "blue" "Checking data flow from sensors to memory..."
    
    # Get data from process cache
    if [ -f "cache/process_sensor/process_cache.json" ]; then
        process_app=$(cat "cache/process_sensor/process_cache.json" | grep -o '"active_app"[[:space:]]*:[[:space:]]*"[^"]*"' | awk -F'"' '{print $4}')
    else
        process_app="N/A"
    fi
    
    # Get data from context file
    if [ -f "memory/last_context.json" ]; then
        context_app=$(cat "memory/last_context.json" | grep -o '"active_app"[[:space:]]*:[[:space:]]*"[^"]*"' | awk -F'"' '{print $4}')
    else
        context_app="N/A"
    fi
    
    # Compare data
    print_colored "blue" "Data flow verification:"
    echo "    Process sensor active app: $process_app"
    echo "    Context file active app: $context_app"
    
    if [ "$process_app" != "N/A" ] && [ "$context_app" != "N/A" ]; then
        if [ "$process_app" == "$context_app" ]; then
            print_colored "green" "✅ Process data is flowing correctly to context"
        else
            print_colored "yellow" "⚠️ Process data might not be flowing to context (different active apps)"
        fi
    else
        print_colored "red" "❌ Cannot verify data flow due to missing data"
    fi
}

# Check LLM context connectivity
check_llm_connectivity() {
    print_colored "blue" "Checking LLM context connectivity..."
    
    # Check if LLM connector is running
    llm_connector_running=false
    if [ -f "pids/llm_context_connector.pid" ]; then
        pid=$(cat "pids/llm_context_connector.pid")
        if ps -p $pid > /dev/null; then
            llm_connector_running=true
        fi
    fi
    
    # Check LLM service is available
    if lsof -ti :8765 &>/dev/null; then
        print_colored "green" "✅ LLM service is running on port 8765"
        llm_service_running=true
    else
        print_colored "red" "❌ LLM service is NOT running on port 8765"
        llm_service_running=false
    fi
    
    # Check LLM connector logs
    if [ -f "logs/llm/llm_context_connector.log" ]; then
        # Check for successful connections
        if grep -q "Connected to LLM service" "logs/llm/llm_context_connector.log"; then
            print_colored "green" "✅ LLM connector has successfully connected to the LLM service"
        else
            print_colored "yellow" "⚠️ No evidence of successful LLM service connection in logs"
        fi
        
        # Check for context updates
        if grep -q "Sent periodic context update" "logs/llm/llm_context_connector.log"; then
            last_context_update=$(grep "Sent periodic context update" "logs/llm/llm_context_connector.log" | tail -1)
            print_colored "green" "✅ Context updates are being sent to LLM"
            print_colored "blue" "Last context update: ${last_context_update#*- }"
        else
            print_colored "yellow" "⚠️ No evidence of context updates being sent to LLM"
        fi
        
        # Check for errors
        recent_errors=$(grep -a "error\|Error\|failed\|Failed" "logs/llm/llm_context_connector.log" | tail -n 3)
        if [ -n "$recent_errors" ]; then
            print_colored "yellow" "Recent errors from LLM connector:"
            echo "$recent_errors" | sed 's/^/    /'
        fi
    else
        if [ "$llm_connector_running" = true ]; then
            print_colored "yellow" "⚠️ LLM connector is running but no log file found"
        else
            print_colored "yellow" "⚠️ No LLM connector log file found"
        fi
    fi
    
    # Display status message
    if [ "$llm_connector_running" = true ] && [ "$llm_service_running" = true ]; then
        if grep -q "Sent periodic context update" "logs/llm/llm_context_connector.log" 2>/dev/null; then
            print_colored "green" "✅ LLM context integration appears to be working"
        else
            print_colored "yellow" "⚠️ LLM context integration is set up but may not be working properly"
        fi
    else
        print_colored "yellow" "⚠️ LLM context integration is incomplete"
        print_colored "blue" "Run ./update_integrated_memory_system.sh to set up LLM context integration"
    fi
}

# Main function
main() {
    print_colored "blue" "===== CONTEXT INTEGRATION SYSTEM STATUS CHECK ====="
    echo ""
    
    # Run checks
    check_services
    echo ""
    check_memory_files
    echo ""
    check_sensor_files
    echo ""
    check_data_flow
    echo ""
    check_llm_connectivity
    echo ""
    
    print_colored "blue" "Checking recent log entries..."
    # Check for recent errors in logs
    if [ -f "logs/monitoring/context_monitor.log" ]; then
        recent_alerts=$(grep -a "⚠️\|❌\|alert\|warning\|error" "logs/monitoring/context_monitor.log" | tail -n 5)
        if [ -n "$recent_alerts" ]; then
            print_colored "yellow" "Recent alerts from monitor:"
            echo "$recent_alerts" | sed 's/^/    /'
        else
            print_colored "green" "✅ No recent alerts from context monitor"
        fi
    fi
    
    print_colored "blue" "===== STATUS CHECK COMPLETE ====="
}

# Run the main function
main