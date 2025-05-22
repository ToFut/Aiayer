#!/bin/bash
# improved_run_integrated_memory_system.sh - Enhanced system to ensure sensor data populates memory and LLM connections work properly

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored text
print_colored() {
    color=$1
    text=$2
    
    case $color in
        "green") echo -e "${GREEN}$text${NC}" ;;
        "yellow") echo -e "${YELLOW}$text${NC}" ;;
        "blue") echo -e "${BLUE}$text${NC}" ;;
        "red") echo -e "${RED}$text${NC}" ;;
        "cyan") echo -e "${CYAN}$text${NC}" ;;
        *) echo "$text" ;;
    esac
}

# Create directories
create_directories() {
    print_colored "blue" "Creating directories..."
    mkdir -p logs/sensors/screen_sensor
    mkdir -p logs/sensors/total_screen
    mkdir -p logs/sensors/process_sensor
    mkdir -p logs/memory
    mkdir -p logs/bridge
    mkdir -p logs/monitoring
    mkdir -p logs/llm
    mkdir -p logs/websocket  # New dedicated directory for websocket logs
    mkdir -p pids
    mkdir -p cache/screen_sensor
    mkdir -p cache/process_sensor
    mkdir -p cache/file_sensor
    mkdir -p memory

    # Set proper permissions
    chmod -R 755 logs
    chmod -R 755 pids
    chmod -R 755 cache
    chmod -R 755 memory
}

# Kill process using a port
kill_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        local pid=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            print_colored "yellow" "Killing process $pid using port $port"
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    else
        print_colored "yellow" "lsof not found. Unable to check ports automatically."
    fi
}

# Kill processes by name with better matching
kill_process() {
    process_name=$1
    pids=$(ps aux | grep -E "${process_name}" | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        print_colored "yellow" "Killing processes matching '${process_name}': $pids"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 1
    fi
}

# Check if a service is installed
check_dependency() {
    local cmd=$1
    local pkg=$2
    
    if ! command -v $cmd &> /dev/null; then
        print_colored "red" "❌ $cmd not found. Please install $pkg."
        return 1
    fi
    return 0
}

# Clean up existing processes
cleanup_existing_processes() {
    print_colored "yellow" "Cleaning up existing processes..."
    
    # Kill processes from PID files
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            print_colored "yellow" "Stopping previous $name (PID: $pid)"
            kill -9 $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    # Kill processes by name - more precise matching to avoid killing unrelated processes
    kill_process "python3.*direct_sensor_to_memory\.py"
    kill_process "python3.*sensors/enhanced_fixed_process_sensor\.py"
    kill_process "python3.*sensors/enhanced_fixed_screen_sensor\.py"
    kill_process "python3.*fixed_bridge_server_enhanced\.py"
    kill_process "python3.*fixed_ws_8765\.py"
    kill_process "python3.*simple_ws_server_8767\.py"
    kill_process "python3.*enhanced_backend_server_8767\.py"
    kill_process "python3.*monitor_context_integration\.py"
    kill_process "python3.*llm_context_connector\.py"
    
    # Clean up ports
    print_colored "yellow" "Cleaning up ports..."
    kill_port 8765  # WebSocket server port
    kill_port 8766  # Bridge server port
    kill_port 8767  # Backend server port
    kill_port 8768  # Enhanced bridge port (if used)
    kill_port 8769  # Memory server port (if used)
    sleep 2
}

# Initialize all required files with proper values
initialize_files() {
    print_colored "blue" "Initializing essential files..."
    timestamp=$(date +%s)
    
    # Initialize context file
    echo '{
        "timestamp": '${timestamp}',
        "active_window": "",
        "active_app": "",
        "active_apps": [],
        "window_history": [],
        "screen_text": ""
    }' > "memory/last_context.json"
    
    # Initialize memory state
    echo '{
        "version": "1.0",
        "last_update": "'$(date -Iseconds)'",
        "context": {
            "active_window": "",
            "active_app": "",
            "active_apps": [],
            "window_history": [],
            "screen_text": ""
        },
        "short_term": [],
        "long_term": [],
        "sensor_data": {
            "screen": {},
            "process": {},
            "file": {}
        }
    }' > "memory/memory_state.json"
    
    # Initialize process cache
    echo '{
        "timestamp": '${timestamp}',
        "active_window": "",
        "active_app": "",
        "active_apps": [],
        "window_history": []
    }' > "cache/process_sensor/process_cache.json"
    
    # Initialize screen cache
    echo '{
        "timestamp": '${timestamp}',
        "screen_text": "",
        "has_images": false,
        "has_videos": false
    }' > "cache/screen_sensor/last_screen.json"
    
    # Initialize file sensor cache
    echo '{
        "timestamp": '${timestamp}',
        "last_file": "",
        "file_content": ""
    }' > "cache/file_sensor/last_file.json"
    
    print_colored "green" "Files prepared"
}

# Fix WebSocket server log path
fix_websocket_server_log_path() {
    # Ensure the WebSocket server logs to the correct file
    print_colored "blue" "Fixing WebSocket server log path..."
    
    if [ -f "fixed_ws_8765.py" ]; then
        # Backup the file
        cp fixed_ws_8765.py fixed_ws_8765.py.bak
        
        # Fix log path to use port 8765 not 8768
        sed -i.path_fix_bak 's/logs\/ws_server_8768\.log/logs\/websocket\/ws_server_8765.log/g' fixed_ws_8765.py
        
        # Check if the fix was applied
        if grep -q "logs/websocket/ws_server_8765.log" fixed_ws_8765.py; then
            print_colored "green" "✅ WebSocket server log path fixed"
        else
            print_colored "yellow" "⚠️ Unable to fix WebSocket server log path automatically"
        fi
    else
        print_colored "yellow" "⚠️ WebSocket server file not found: fixed_ws_8765.py"
    fi
}

# Fix port configuration in all components
fix_port_configuration() {
    print_colored "blue" "Fixing port configuration in components..."
    
    # Fix bridge server ports
    if [ -f "fixed_bridge_server_enhanced.py" ]; then
        sed -i.bak 's/WS_PORT = 8768/WS_PORT = 8766/' fixed_bridge_server_enhanced.py
        sed -i.bak 's/MEMORY_SERVER_PORT = 8769/MEMORY_SERVER_PORT = 8767/' fixed_bridge_server_enhanced.py
        print_colored "green" "✅ Bridge server ports configured"
    else
        print_colored "yellow" "⚠️ Bridge server file not found"
    fi
    
    # Fix sensor ports
    for sensor_file in "sensors/enhanced_fixed_process_sensor.py" "sensors/enhanced_fixed_screen_sensor.py"; do
        if [ -f "$sensor_file" ]; then
            sed -i.bak 's/bridge_uri="ws:\/\/localhost:8765"/bridge_uri="ws:\/\/localhost:8766"/' "$sensor_file"
            print_colored "green" "✅ Sensor port configured in $sensor_file"
        else
            print_colored "yellow" "⚠️ Sensor file not found: $sensor_file"
        fi
    done
    
    # Fix client type handling in WebSocket server
    if [ -f "fixed_ws_8765.py" ]; then
        # Check if the client type handling is correct
        if ! grep -q "client_type == 'chat_overlay' or client_type == 'ui'" fixed_ws_8765.py; then
            # Create backup of the file
            cp fixed_ws_8765.py fixed_ws_8765.py.client_type_bak
            
            # Update client type handling to recognize both 'ui' and 'chat_overlay'
            sed -i.bak 's/if client_type == "llm"/if client_type == "llm"/g' fixed_ws_8765.py
            sed -i.bak 's/elif client_type == "chat_overlay"/elif client_type == "chat_overlay" or client_type == "ui"/g' fixed_ws_8765.py
            
            # Ensure client_type extraction handles nested messages
            if ! grep -q "client_type = data.get('client_type', data.get('payload', {}).get('client_type', 'unknown'))" fixed_ws_8765.py; then
                print_colored "yellow" "⚠️ Manual update needed for client_type extraction in fixed_ws_8765.py"
                print_colored "cyan" "Please ensure the register message handler extracts client_type from both top-level and payload"
            else
                print_colored "green" "✅ Client type handling is already correct"
            fi
        else
            print_colored "green" "✅ Client type handling already fixed"
        fi
    else
        print_colored "yellow" "⚠️ WebSocket server file not found: fixed_ws_8765.py"
    fi
}

# Start a service and capture its PID with better error handling
start_service() {
    service_name=$1
    command=$2
    log_file=$3
    pid_file=$4
    
    print_colored "blue" "Starting $service_name..."
    mkdir -p $(dirname "$log_file")
    
    # Execute the command and redirect output
    eval "$command > $log_file 2>&1 &"
    pid=$!
    echo $pid > $pid_file
    
    # Wait for process to start and verify it's running
    sleep 2
    if ps -p $pid > /dev/null; then
        print_colored "green" "✅ $service_name started with PID: $pid"
        return 0
    else
        # Check for error messages in the log
        if [ -f "$log_file" ]; then
            error_msg=$(tail -10 "$log_file" | grep -i "error")
            if [ ! -z "$error_msg" ]; then
                print_colored "red" "❌ $service_name failed to start with error:"
                print_colored "red" "$error_msg"
            else
                print_colored "red" "❌ $service_name failed to start. Check $log_file for details."
            fi
        else
            print_colored "red" "❌ $service_name failed to start and no log file was created."
        fi
        return 1
    fi
}

# Start all services in the correct order with dependency checks
start_services() {
    print_colored "blue" "Starting services in the correct sequence..."
    services_started=true
    
    # Start service with dependency check and better error handling
    start_service_with_dependency() {
        service_name=$1
        command=$2
        log_file=$3
        pid_file=$4
        dependency_check=$5
        
        # Check if service file exists
        if [[ -n "$dependency_check" && ! -f "$dependency_check" ]]; then
            print_colored "red" "❌ $service_name dependency file not found: $dependency_check"
            services_started=false
            return 1
        fi
        
        # Start the service
        start_service "$service_name" "$command" "$log_file" "$pid_file"
        result=$?
        
        if [ $result -ne 0 ]; then
            services_started=false
            return 1
        fi
        return 0
    }
    
    # 1. Start WebSocket server - foundational service
    start_service_with_dependency "WebSocket Server" "python3 fixed_ws_8765.py" "logs/websocket/ws_server_8765.log" "pids/ws_server.pid" "fixed_ws_8765.py"
    WS_RESULT=$?
    
    # Wait for WebSocket server to initialize
    sleep 3
    
    # 2. Start bridge server - depends on WebSocket
    if [ $WS_RESULT -eq 0 ]; then
        start_service_with_dependency "Bridge Server" "python3 fixed_bridge_server_enhanced.py" "logs/bridge/bridge_server.log" "pids/bridge_server.pid" "fixed_bridge_server_enhanced.py"
        BRIDGE_RESULT=$?
    else
        print_colored "red" "❌ Skipping Bridge Server - WebSocket server not started"
        BRIDGE_RESULT=1
    fi
    
    # Wait for bridge server to initialize
    sleep 3
    
    # 3. Start enhanced backend server - can start independently
    start_service_with_dependency "Enhanced Backend Server" "python3 enhanced_backend_server_8767.py" "logs/backend/enhanced_backend_server.log" "pids/backend_server.pid" "enhanced_backend_server_8767.py"
    BACKEND_RESULT=$?
    
    # Wait for servers to initialize
    sleep 3
    
    # 4. Start sensors - depend on bridge server
    if [ $BRIDGE_RESULT -eq 0 ]; then
        start_service_with_dependency "Process Sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor/process_sensor.log" "pids/process_sensor.pid" "sensors/enhanced_fixed_process_sensor.py"
        PROCESS_RESULT=$?
        
        start_service_with_dependency "Total Screen Analyzer" "python3 sensors/total_screen_analyzer.py" "logs/sensors/total_screen/total_screen_analyzer.log" "pids/total_screen_analyzer.pid" "sensors/total_screen_analyzer.py"
        SCREEN_RESULT=$?
    else
        print_colored "red" "❌ Skipping sensors - Bridge server not started"
        PROCESS_RESULT=1
        SCREEN_RESULT=1
    fi
    
    # Wait for sensors to initialize
    sleep 3
    
    # 5. Start direct sensor to memory integration - depends on sensors
    if [ $PROCESS_RESULT -eq 0 ] || [ $SCREEN_RESULT -eq 0 ]; then
        start_service_with_dependency "Direct Sensor-Memory Integration" "python3 direct_sensor_to_memory.py" "logs/memory/direct_integration.log" "pids/direct_sensor_memory.pid" "direct_sensor_to_memory.py"
        DIRECT_RESULT=$?
    else
        print_colored "red" "❌ Skipping Direct Sensor-Memory Integration - Sensors not started"
        DIRECT_RESULT=1
    fi
    
    # 6. Start LLM context connector - depends on WebSocket server
    if [ $WS_RESULT -eq 0 ]; then
        start_service_with_dependency "LLM Context Connector" "python3 llm_context_connector.py" "logs/llm/llm_context.log" "pids/llm_context.pid" "llm_context_connector.py"
        LLM_RESULT=$?
    else
        print_colored "red" "❌ Skipping LLM Context Connector - WebSocket server not started"
        LLM_RESULT=1
    fi
    
    # 7. Start monitor - can start independently
    start_service_with_dependency "Context Integration Monitor" "python3 monitor_context_integration.py" "logs/monitoring/context_monitor.log" "pids/context_monitor.pid" "monitor_context_integration.py"
    MONITOR_RESULT=$?
    
    # Return results for verification
    export WS_RESULT=$WS_RESULT
    export BRIDGE_RESULT=$BRIDGE_RESULT
    export BACKEND_RESULT=$BACKEND_RESULT
    export PROCESS_RESULT=$PROCESS_RESULT
    export SCREEN_RESULT=$SCREEN_RESULT
    export DIRECT_RESULT=$DIRECT_RESULT
    export LLM_RESULT=$LLM_RESULT
    export MONITOR_RESULT=$MONITOR_RESULT
    
    if [ "$services_started" = true ]; then
        return 0
    else
        return 1
    fi
}

# Verify all services are running correctly
verify_services() {
    print_colored "blue" "Verifying services..."
    all_ok=true
    
    # Check each service
    if [ $WS_RESULT -ne 0 ]; then
        print_colored "red" "❌ WebSocket server failed to start"
        all_ok=false
    fi
    
    if [ $BRIDGE_RESULT -ne 0 ]; then
        print_colored "red" "❌ Bridge server failed to start"
        all_ok=false
    fi
    
    if [ $BACKEND_RESULT -ne 0 ]; then
        print_colored "red" "❌ Backend server failed to start"
        all_ok=false
    fi
    
    if [ $PROCESS_RESULT -ne 0 ]; then
        print_colored "red" "❌ Process sensor failed to start"
        all_ok=false
    fi
    
    if [ $SCREEN_RESULT -ne 0 ]; then
        print_colored "red" "❌ Screen sensor failed to start"
        all_ok=false
    fi
    
    if [ $DIRECT_RESULT -ne 0 ]; then
        print_colored "red" "❌ Direct sensor-memory integration failed to start"
        all_ok=false
    fi
    
    if [ $LLM_RESULT -ne 0 ]; then
        print_colored "red" "❌ LLM context connector failed to start"
        all_ok=false
    fi
    
    if [ $MONITOR_RESULT -ne 0 ]; then
        print_colored "red" "❌ Context integration monitor failed to start"
        all_ok=false
    fi
    
    # Verify port bindings more thoroughly
    print_colored "blue" "Verifying port bindings..."
    
    # Check WebSocket server port
    if command -v lsof &> /dev/null && lsof -ti :8765 &>/dev/null; then
        print_colored "green" "✅ WebSocket server is running on port 8765"
    else
        print_colored "red" "❌ WebSocket server is not running on port 8765"
        all_ok=false
    fi
    
    # Check Bridge server port
    if command -v lsof &> /dev/null && lsof -ti :8766 &>/dev/null; then
        print_colored "green" "✅ Bridge server is running on port 8766"
    else
        print_colored "red" "❌ Bridge server is not running on port 8766"
        all_ok=false
    fi
    
    # Check Backend server port
    if command -v lsof &> /dev/null && lsof -ti :8767 &>/dev/null; then
        print_colored "green" "✅ Backend server is running on port 8767"
    else
        print_colored "red" "❌ Backend server is not running on port 8767"
        all_ok=false
    fi
    
    # Return the status
    if [ "$all_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

# Verify memory is being populated
verify_memory_population() {
    print_colored "blue" "Verifying memory population..."
    
    # Check memory state file size
    if [ -f "memory/memory_state.json" ]; then
        size=$(wc -c < "memory/memory_state.json")
        if [ $size -gt 200 ]; then
            print_colored "green" "✅ Memory state file has data ($size bytes)"
        else
            print_colored "red" "❌ Memory state file may be empty ($size bytes)"
        fi
    else
        print_colored "red" "❌ Memory state file does not exist"
    fi
    
    # Check context file
    if [ -f "memory/last_context.json" ]; then
        size=$(wc -c < "memory/last_context.json")
        if [ $size -gt 200 ]; then
            print_colored "green" "✅ Context file has data ($size bytes)"
            
            # Show context info
            print_colored "blue" "Context information:"
            cat "memory/last_context.json" | grep -E "active_window|active_app|timestamp" | sed 's/^/    /'
        else
            print_colored "red" "❌ Context file may be empty ($size bytes)"
        fi
    else
        print_colored "red" "❌ Context file does not exist"
    fi
}

# Check LLM context integration
verify_llm_context_integration() {
    print_colored "blue" "Verifying LLM context integration..."
    
    if [ -f "logs/llm/llm_context.log" ]; then
        if grep -q "Sent periodic context update" "logs/llm/llm_context.log"; then
            print_colored "green" "✅ LLM context connector is sending updates"
            
            # Show last context update time
            last_update=$(grep "Sent periodic context update" "logs/llm/llm_context.log" | tail -1 | sed 's/.*\[\(.*\)\].*/\1/')
            print_colored "blue" "Last context update: $last_update"
            
            # Check WebSocket connection
            if grep -q "Connected to LLM service at ws://localhost:8765" "logs/llm/llm_context.log"; then
                print_colored "green" "✅ LLM context connector successfully connected to WebSocket"
            else
                print_colored "red" "❌ LLM context connector may have connection issues with WebSocket"
            fi
        else
            print_colored "red" "❌ No LLM context updates found in logs"
        fi
    else
        print_colored "red" "❌ LLM context log file does not exist"
    fi
    
    # Check WebSocket logs for client registration
    if [ -f "logs/websocket/ws_server_8765.log" ]; then
        if grep -q "LLM service connected" "logs/websocket/ws_server_8765.log"; then
            print_colored "green" "✅ WebSocket server recognized LLM service connection"
        else
            print_colored "red" "❌ WebSocket server did not register LLM service connection"
        fi
        
        if grep -q "Chat overlay connected" "logs/websocket/ws_server_8765.log"; then
            print_colored "green" "✅ WebSocket server recognized chat overlay connection"
        else
            print_colored "yellow" "⚠️ WebSocket server has not yet registered a chat overlay connection"
            print_colored "cyan" "This is normal if you haven't launched the overlay app yet"
        fi
    else
        print_colored "red" "❌ WebSocket log file does not exist"
    fi
}

# Show overlay connection instructions
show_overlay_instructions() {
    print_colored "yellow" "========================================================"
    print_colored "yellow" "Instructions for connecting the overlay application:"
    print_colored "cyan" "1. The WebSocket server is running on port 8765"
    print_colored "cyan" "2. Make sure your overlay connects to: ws://localhost:8765"
    print_colored "cyan" "3. The overlay should register with type 'ui' or 'chat_overlay'"
    print_colored "cyan" "4. When the overlay receives 'registration_confirmed', it should update its connection status"
    print_colored "cyan" "5. Run start_next_gen_overlay.sh or start_eye_overlay.sh to launch the overlay"
    print_colored "yellow" "========================================================"
}

# Display monitoring instructions
show_monitoring_instructions() {
    print_colored "yellow" "To monitor the system:"
    echo "tail -f logs/memory/direct_integration.log          # Direct integration logs"
    echo "tail -f logs/bridge/bridge_server.log               # Bridge server logs"
    echo "tail -f logs/monitoring/context_monitor.log         # Context monitor logs"
    echo "tail -f logs/sensors/process_sensor/process_sensor.log     # Process sensor logs"
    echo "tail -f logs/sensors/screen_sensor/screen_sensor.log       # Screen sensor logs"
    echo "tail -f logs/llm/llm_context.log                    # LLM context connector logs"
    echo "tail -f logs/websocket/ws_server_8765.log           # WebSocket server logs"
    echo "tail -f logs/backend/backend_server.log             # Backend server logs"
}

# Run the system with proper cleanup on exit
run_system() {
    # Keep the script running
    print_colored "blue" "Press Ctrl+C to stop all services"
    
    # Set up trap for clean exit
    trap cleanup_on_exit INT TERM
    
    # Keep the script running
    while true; do
        sleep 5
        
        # Periodically check that all services are still running
        if ! check_services_health; then
            print_colored "yellow" "Warning: Some services may have stopped. Use Ctrl+C to exit and restart."
        fi
    done
}

# Check if services are still running
check_services_health() {
    all_healthy=true
    
    # Check each service is still running based on PID files
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            
            if ! ps -p $pid > /dev/null; then
                print_colored "red" "❌ Service $name (PID: $pid) has stopped"
                all_healthy=false
            fi
        fi
    done
    
    # Check WebSocket is still responding
    if command -v curl &> /dev/null; then
        # For a more thorough check, we could attempt a WebSocket connection
        # This is a simple check if the port is still in use
        if ! lsof -ti :8765 &>/dev/null; then
            print_colored "red" "❌ WebSocket server on port 8765 is not responding"
            all_healthy=false
        fi
    fi
    
    if [ "$all_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

# Clean up on exit
cleanup_on_exit() {
    print_colored "yellow" "Stopping all services..."
    
    # Stop each service based on PID files
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            print_colored "yellow" "Stopping $name (PID: $pid)"
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    print_colored "green" "System shutdown complete"
    exit 0
}

# MAIN FUNCTION
main() {
    print_colored "blue" "=================================================="
    print_colored "blue" "Starting Integrated Memory System with LLM Context"
    print_colored "blue" "=================================================="
    
    # Check for required dependencies
    check_dependency "python3" "Python 3" || { print_colored "red" "Python 3 is required to run this system."; exit 1; }
    check_dependency "lsof" "lsof utility" || print_colored "yellow" "Warning: lsof not found. Port checking will be limited."
    
    # Create essential directories
    create_directories
    
    # Clean up existing processes
    cleanup_existing_processes
    
    # Initialize files
    initialize_files
    
    # Fix WebSocket server log path
    fix_websocket_server_log_path
    
    # Fix port configuration
    fix_port_configuration
    
    # Start services
    print_colored "blue" "Starting services..."
    start_services
    service_start_result=$?
    
    # Verify services
    verify_services
    service_verify_result=$?
    
    # Wait for system to start collecting data
    if [ $service_verify_result -eq 0 ]; then
        print_colored "blue" "Waiting 15 seconds for data collection..."
        sleep 15
        
        # Verify memory population
        verify_memory_population
        
        # Verify LLM context integration
        verify_llm_context_integration
    else
        print_colored "yellow" "System started with some components missing"
        print_colored "yellow" "Check the logs for specific issues"
    fi
    
    # Show instructions for overlay
    show_overlay_instructions
    
    # Show monitoring instructions
    show_monitoring_instructions
    
    # Final status
    if [ $service_verify_result -eq 0 ]; then
        print_colored "green" "=================================================="
        print_colored "green" "✅ Integrated memory system is now running!"
        print_colored "green" "=================================================="
    else
        print_colored "yellow" "=================================================="
        print_colored "yellow" "⚠️ System started with issues"
        print_colored "yellow" "=================================================="
    fi
    
    # Run the system
    run_system
}

# Execute main function
main