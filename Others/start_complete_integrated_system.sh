#!/bin/bash

# Complete Integrated System Startup Script
# Starts all system components in proper order with dependency management

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"
PYTHON_CMD="python3"

# Port configuration
WS_PORT=8765
BACKEND_PORT=8767
LLM_PORT=8766
BRIDGE_PORT=8080

# Component PIDs (using regular array instead of associative)
COMPONENT_PIDS=()

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p "$LOG_DIR"/{websocket,backend,memory,sensors,llm,bridge}
    mkdir -p "$PID_DIR"
    mkdir -p "$SCRIPT_DIR/cache"/{screen_sensor,process_sensor,app_detection,file_sensor,llava_processor}
    mkdir -p "$SCRIPT_DIR/results"
    mkdir -p "$SCRIPT_DIR/static"
    log "Directories created successfully"
}

# Check Python dependencies
check_dependencies() {
    log "Checking Python dependencies..."
    
    local required_packages=(
        "websockets"
        "psutil" 
        "aiohttp"
        "mss"
        "PIL"
        "numpy"
        "sentence-transformers"
        "pytesseract"
        "cv2"
    )
    
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        warn "Missing packages: ${missing_packages[*]}"
        info "Installing missing packages..."
        
        # Install requirements
        if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
            $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"
        fi
        
        # Install additional packages
        for package in "${missing_packages[@]}"; do
            case $package in
                "PIL")
                    $PYTHON_CMD -m pip install Pillow
                    ;;
                "cv2")
                    $PYTHON_CMD -m pip install opencv-python
                    ;;
                *)
                    $PYTHON_CMD -m pip install "$package"
                    ;;
            esac
        done
    fi
    
    log "Dependencies check completed"
}

# Kill existing processes
cleanup_processes() {
    log "Cleaning up existing processes..."
    
    # Kill processes by port
    local ports=($WS_PORT $BACKEND_PORT $LLM_PORT $BRIDGE_PORT)
    for port in "${ports[@]}"; do
        if lsof -ti :$port >/dev/null 2>&1; then
            warn "Killing processes on port $port"
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # Kill by process name patterns
    local patterns=("fixed_ws_8765" "enhanced_backend" "self_contained_llm" "screen_sensor" "process_sensor")
    for pattern in "${patterns[@]}"; do
        pkill -f "$pattern" 2>/dev/null || true
    done
    
    # Clean PID files
    rm -f "$PID_DIR"/*.pid
    
    sleep 2
    log "Cleanup completed"
}

# Check if port is available
is_port_available() {
    local port=$1
    ! lsof -ti :$port >/dev/null 2>&1
}

# Wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    info "Waiting for $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if ! is_port_available $port; then
            log "$service_name is ready on port $port"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            info "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi
        
        sleep 1
        ((attempt++))
    done
    
    error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Start LLM service
start_llm_service() {
    log "Starting LLM service on port $LLM_PORT..."
    
    if [ ! -f "$SCRIPT_DIR/self_contained_llm_ws.py" ]; then
        error "LLM service file not found: self_contained_llm_ws.py"
        return 1
    fi
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/self_contained_llm_ws.py" \
        > "$LOG_DIR/llm/llm_service.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/llm_service.pid"
    echo "llm_service:$pid" >> "$PID_DIR/components.txt"
    
    # Wait for service to start
    if wait_for_service "LLM service" $LLM_PORT; then
        log "LLM service started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start LLM service"
        return 1
    fi
}

# Start memory system
start_memory_system() {
    log "Starting memory system..."
    
    # Initialize memory state if not exists
    local memory_state_file="$SCRIPT_DIR/memory/memory_state.json"
    if [ ! -f "$memory_state_file" ]; then
        info "Creating initial memory state file..."
        mkdir -p "$(dirname "$memory_state_file")"
        cat > "$memory_state_file" << 'EOF'
{
    "version": "1.0",
    "last_update": "2025-01-21T00:00:00",
    "context": {
        "active_window": "",
        "active_app": "",
        "screen_text": ""
    },
    "short_term": [],
    "long_term": [],
    "sensor_data": {
        "screen": {
            "timestamp": "2025-01-21T00:00:00",
            "active_window": "",
            "active_app": "",
            "window_history": []
        },
        "process": {
            "timestamp": "2025-01-21T00:00:00", 
            "active_apps": [],
            "window_history": []
        }
    }
}
EOF
    fi
    
    log "Memory system initialized"
}

# Start process sensor
start_process_sensor() {
    log "Starting process sensor..."
    
    if [ ! -f "$SCRIPT_DIR/sensors/process_sensor.py" ]; then
        error "Process sensor not found: sensors/process_sensor.py"
        return 1
    fi
    
    # Create sensor startup script
    cat > "$SCRIPT_DIR/run_process_sensor.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sensors.process_sensor import ProcessSensor

async def main():
    config = {
        'interval_sec': 5,
        'exclude_patterns': ['kernel', 'system', 'daemon']
    }
    
    sensor = ProcessSensor(config)
    if await sensor.start():
        print("Process sensor started successfully")
        # Keep running
        while True:
            await asyncio.sleep(1)
    else:
        print("Failed to start process sensor")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/run_process_sensor.py" \
        > "$LOG_DIR/sensors/process_sensor.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/process_sensor.pid"
    COMPONENT_PIDS[process_sensor]=$pid
    
    log "Process sensor started (PID: $pid)"
}

# Start screen sensor
start_screen_sensor() {
    log "Starting screen sensor..."
    
    if [ ! -f "$SCRIPT_DIR/sensors/screen_sensor.py" ]; then
        error "Screen sensor not found: sensors/screen_sensor.py"
        return 1
    fi
    
    # Create sensor startup script
    cat > "$SCRIPT_DIR/run_screen_sensor.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sensors.screen_sensor import ScreenSensor

async def main():
    config = {
        'interval_sec': 3,
        'max_memory_mb': 50
    }
    
    sensor = ScreenSensor(config)
    if await sensor.initialize():
        sensor.start()
        print("Screen sensor started successfully")
        # Keep running
        while True:
            await asyncio.sleep(1)
    else:
        print("Failed to start screen sensor")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/run_screen_sensor.py" \
        > "$LOG_DIR/sensors/screen_sensor.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/screen_sensor.pid"
    COMPONENT_PIDS[screen_sensor]=$pid
    
    log "Screen sensor started (PID: $pid)"
}

# Start backend server
start_backend_server() {
    log "Starting backend server on port $BACKEND_PORT..."
    
    if [ ! -f "$SCRIPT_DIR/backend/enhanced_backend_server.py" ]; then
        error "Backend server not found: backend/enhanced_backend_server.py"
        return 1
    fi
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/backend/enhanced_backend_server.py" \
        > "$LOG_DIR/backend/backend_server.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/backend_server.pid"
    COMPONENT_PIDS[backend_server]=$pid
    
    # Wait for service to start
    if wait_for_service "Backend server" $BACKEND_PORT; then
        log "Backend server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start backend server"
        return 1
    fi
}

# Start WebSocket server
start_websocket_server() {
    log "Starting WebSocket server on port $WS_PORT..."
    
    if [ ! -f "$SCRIPT_DIR/fixed_ws_8765.py" ]; then
        error "WebSocket server not found: fixed_ws_8765.py"
        return 1
    fi
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/fixed_ws_8765.py" \
        > "$LOG_DIR/websocket/ws_server.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/ws_server.pid"
    COMPONENT_PIDS[ws_server]=$pid
    
    # Wait for service to start
    if wait_for_service "WebSocket server" $WS_PORT; then
        log "WebSocket server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start WebSocket server"
        return 1
    fi
}

# Start brain router integration
start_brain_router() {
    log "Starting brain router integration..."
    
    # Create brain router startup script
    cat > "$SCRIPT_DIR/run_brain_router.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from brain.core.brain_router import brain_router, process_chat_request
from brain.handlers.ask_mode_handler import handle_ask_mode
from brain.handlers.agent_mode_handler import handle_agent_mode

async def main():
    print("Brain router system starting...")
    
    # Register specialized handlers
    brain_router.register_handler("Ask", handle_ask_mode)
    brain_router.register_handler("Agent", handle_agent_mode)
    
    print("Brain router handlers registered")
    print("Brain router system ready")
    
    # Test the system
    test_result = await process_chat_request(
        mode="Ask",
        query="System status check",
        user_id="system",
        session_id="startup"
    )
    
    print(f"Brain router test result: {test_result['success']}")
    
    # Keep running
    while True:
        await asyncio.sleep(10)
        status = brain_router.get_system_status()
        print(f"System health: {status['system_health']}")

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    nohup $PYTHON_CMD "$SCRIPT_DIR/run_brain_router.py" \
        > "$LOG_DIR/brain_router.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/brain_router.pid"
    COMPONENT_PIDS[brain_router]=$pid
    
    log "Brain router started (PID: $pid)"
}

# Start overlay system
start_overlay_system() {
    log "Starting overlay system..."
    
    # Check if overlay files exist
    local overlay_files=(
        "futuristic_overlay.html"
        "eye_widget_overlay.html"
        "templates/index.html"
    )
    
    local available_overlay=""
    for file in "${overlay_files[@]}"; do
        if [ -f "$SCRIPT_DIR/$file" ]; then
            available_overlay="$file"
            break
        fi
    done
    
    if [ -z "$available_overlay" ]; then
        warn "No overlay files found, skipping overlay system"
        return 0
    fi
    
    # Start simple HTTP server for overlay
    if command -v python3 >/dev/null 2>&1; then
        cd "$SCRIPT_DIR"
        nohup python3 -m http.server $BRIDGE_PORT \
            > "$LOG_DIR/bridge/overlay_server.log" 2>&1 &
        
        local pid=$!
        echo $pid > "$PID_DIR/overlay_server.pid"
        COMPONENT_PIDS[overlay_server]=$pid
        
        log "Overlay server started on port $BRIDGE_PORT (PID: $pid)"
        info "Access overlay at: http://localhost:$BRIDGE_PORT/$available_overlay"
    else
        warn "Python3 not found, overlay server not started"
    fi
}

# Test system connectivity
test_system_connectivity() {
    log "Testing system connectivity..."
    
    local services=(
        "LLM service:$LLM_PORT"
        "Backend server:$BACKEND_PORT" 
        "WebSocket server:$WS_PORT"
        "Overlay server:$BRIDGE_PORT"
    )
    
    local all_good=true
    
    for service_info in "${services[@]}"; do
        local service_name=$(echo "$service_info" | cut -d: -f1)
        local port=$(echo "$service_info" | cut -d: -f2)
        
        if is_port_available $port; then
            error "$service_name is not responding on port $port"
            all_good=false
        else
            log "$service_name is responding on port $port"
        fi
    done
    
    if $all_good; then
        log "All services are responding correctly"
        return 0
    else
        error "Some services are not responding"
        return 1
    fi
}

# Display system status
show_system_status() {
    echo
    log "=== System Status ==="
    echo
    
    echo -e "${BLUE}Running Components:${NC}"
    for component in "${!COMPONENT_PIDS[@]}"; do
        local pid=${COMPONENT_PIDS[$component]}
        if kill -0 $pid 2>/dev/null; then
            echo -e "  ✅ $component (PID: $pid)"
        else
            echo -e "  ❌ $component (PID: $pid - not running)"
        fi
    done
    
    echo
    echo -e "${BLUE}Service Endpoints:${NC}"
    echo -e "  🌐 WebSocket Server: ws://localhost:$WS_PORT"
    echo -e "  🔧 Backend Server: ws://localhost:$BACKEND_PORT"
    echo -e "  🤖 LLM Service: ws://localhost:$LLM_PORT"
    echo -e "  📱 Overlay Interface: http://localhost:$BRIDGE_PORT"
    
    echo
    echo -e "${BLUE}Log Files:${NC}"
    echo -e "  📄 WebSocket: $LOG_DIR/websocket/ws_server.log"
    echo -e "  📄 Backend: $LOG_DIR/backend/backend_server.log"
    echo -e "  📄 LLM: $LOG_DIR/llm/llm_service.log"
    echo -e "  📄 Sensors: $LOG_DIR/sensors/"
    
    echo
    echo -e "${BLUE}Control Commands:${NC}"
    echo -e "  🛑 Stop System: ./stop_system.sh"
    echo -e "  📊 Monitor Logs: tail -f $LOG_DIR/websocket/ws_server.log"
    echo -e "  🔍 Check Status: ps aux | grep -E '(fixed_ws|enhanced_backend|self_contained)'"
    
    echo
}

# Create stop script
create_stop_script() {
    cat > "$SCRIPT_DIR/stop_system.sh" << 'EOF'
#!/bin/bash

# Stop all system components

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log "Stopping system components..."

# Stop by PID files
if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            component=$(basename "$pid_file" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                log "Stopping $component (PID: $pid)"
                kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
            fi
            
            rm -f "$pid_file"
        fi
    done
fi

# Kill by port
for port in 8765 8766 8767 8080; do
    if lsof -ti :$port >/dev/null 2>&1; then
        log "Killing processes on port $port"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

# Kill by process pattern
for pattern in "fixed_ws_8765" "enhanced_backend" "self_contained_llm" "screen_sensor" "process_sensor" "brain_router"; do
    pkill -f "$pattern" 2>/dev/null || true
done

log "System stopped"
EOF
    
    chmod +x "$SCRIPT_DIR/stop_system.sh"
}

# Signal handlers
cleanup_on_exit() {
    echo
    warn "Received interrupt signal, cleaning up..."
    "$SCRIPT_DIR/stop_system.sh"
    exit 0
}

trap cleanup_on_exit INT TERM

# Main execution
main() {
    log "Starting Complete Integrated System..."
    echo
    
    # Pre-flight checks
    create_directories
    check_dependencies
    cleanup_processes
    
    # Initialize core systems
    start_memory_system
    
    # Start services in dependency order
    if start_llm_service; then
        sleep 2
        
        if start_backend_server; then
            sleep 2
            
            if start_websocket_server; then
                sleep 2
                
                # Start supporting components
                start_process_sensor
                start_screen_sensor
                start_brain_router
                start_overlay_system
                
                sleep 3
                
                # Test connectivity
                if test_system_connectivity; then
                    create_stop_script
                    show_system_status
                    
                    log "🎉 System startup completed successfully!"
                    echo
                    info "The system is now running. Press Ctrl+C to stop all components."
                    
                    # Keep script running
                    while true; do
                        sleep 10
                        # Optional: Add health checks here
                    done
                else
                    error "System connectivity test failed"
                    cleanup_on_exit
                    exit 1
                fi
            else
                error "Failed to start WebSocket server"
                cleanup_on_exit
                exit 1
            fi
        else
            error "Failed to start backend server"
            cleanup_on_exit
            exit 1
        fi
    else
        error "Failed to start LLM service"
        cleanup_on_exit
        exit 1
    fi
}

# Run main function
main "$@"