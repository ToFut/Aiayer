#!/bin/bash

# Enhanced Agent-Based LLM WebSocket Server Startup Script
# This script starts the agent-based WebSocket server with all necessary components
# - Initializes cache directories and memory system
# - Sets up sensors for screen, process, and file monitoring
# - Handles auto-cleanup for logs and cache files
# - Manages memory usage to prevent OOM issues

# Colors and formatting
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Log prefix
log_prefix() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Success message
success() {
    log_prefix "${GREEN}✅ $1${NC}"
}

# Warning message
warning() {
    log_prefix "${YELLOW}⚠️ $1${NC}"
}

# Error message
error() {
    log_prefix "${RED}❌ $1${NC}"
}

# Info message
info() {
    log_prefix "${BOLD}$1${NC}"
}

# Debug message (more detail)
debug() {
    log_prefix "${CYAN}🔍 $1${NC}"
}

# Run a command with logging and error handling
run_cmd() {
    local cmd="$1"
    local msg="$2"
    local show_output="${3:-false}"  # Optional parameter to show output
    
    info "$msg"
    
    if [ "$show_output" = "true" ]; then
        # Run command and show output
        eval "$cmd" || {
            error "Command failed: $cmd"
            return 1
        }
    else
        # Run command silently
        eval "$cmd" > /dev/null 2>&1 || {
            error "Command failed: $cmd"
            return 1
        }
    fi
    
    return 0
}

# Ensure directories exist
ensure_directories() {
    info "Creating necessary directories..."
    
    # Create core directories
    mkdir -p logs pids memory/logs memory/sensor_data
    mkdir -p cache/screen_sensor cache/process_sensor cache/file_sensor
    mkdir -p config/backups
    
    # Create memory system directories
    mkdir -p memory/memory memory/vector_db
    
    success "Created all necessary directories"
}

# Set limits
MAX_CACHE_SIZE_MB=500           # Maximum cache directory size in MB
MAX_LOGS_SIZE_MB=200            # Maximum logs directory size in MB
MAX_BACKUP_FILES=10             # Maximum number of backup files to keep
MIN_DISK_SPACE_PERCENT=10       # Minimum free disk space percentage
MAX_MEMORY_SIZE_MB=1000         # Maximum memory usage for the process in MB

# Check disk space
check_disk_space() {
    local dir="$1"
    local min_percent="$2"
    
    # Get available disk space percentage
    local avail_percent=$(df -h "$dir" | awk 'NR==2 {print $5}' | sed 's/%//')
    local free_percent=$((100 - avail_percent))
    
    if [ "$free_percent" -lt "$min_percent" ]; then
        warning "Low disk space! Only ${free_percent}% available (minimum ${min_percent}%)"
        return 1
    fi
    
    info "Disk space check passed: ${free_percent}% available"
    return 0
}

# Clean old log files
clean_logs() {
    info "Checking log size and cleaning old logs..."
    
    # Get total size of logs directory in MB
    local logs_size=$(du -sm logs | cut -f1)
    
    if [ "$logs_size" -gt "$MAX_LOGS_SIZE_MB" ]; then
        warning "Logs directory exceeds ${MAX_LOGS_SIZE_MB}MB (current: ${logs_size}MB). Cleaning..."
        
        # Delete oldest log files based on modification time
        find logs -type f -name "*.log*" -mtime +7 -delete
        
        # If still too large, compress files older than 3 days
        local new_size=$(du -sm logs | cut -f1)
        if [ "$new_size" -gt "$MAX_LOGS_SIZE_MB" ]; then
            find logs -type f -name "*.log" -mtime +3 -exec gzip {} \;
        fi
    else
        success "Logs size is within limits (${logs_size}MB / ${MAX_LOGS_SIZE_MB}MB)"
    fi
    
    # Also clean memory logs
    if [ -d "memory/logs" ]; then
        local memory_logs_size=$(du -sm memory/logs | cut -f1)
        if [ "$memory_logs_size" -gt "50" ]; then  # 50MB limit for memory logs
            warning "Memory logs directory exceeds 50MB (current: ${memory_logs_size}MB). Cleaning..."
            find memory/logs -type f -name "*.log*" -mtime +3 -delete
        fi
    fi
}

# Clean cache files
clean_cache() {
    info "Checking cache size and cleaning old cache files..."
    
    # Get total size of cache directory in MB
    local cache_size=$(du -sm cache | cut -f1)
    
    if [ "$cache_size" -gt "$MAX_CACHE_SIZE_MB" ]; then
        warning "Cache directory exceeds ${MAX_CACHE_SIZE_MB}MB (current: ${cache_size}MB). Cleaning..."
        
        # Keep only the most recent MAX_BACKUP_FILES backup files in each sensor directory
        for sensor_dir in cache/*_sensor; do
            if [ -d "$sensor_dir" ]; then
                # Count backup files
                local backup_count=$(find "$sensor_dir" -name "*.bak_*" | wc -l)
                
                if [ "$backup_count" -gt "$MAX_BACKUP_FILES" ]; then
                    # Keep only the newest MAX_BACKUP_FILES backup files
                    find "$sensor_dir" -name "*.bak_*" | sort | head -n -"$MAX_BACKUP_FILES" | xargs rm -f
                    success "Cleaned old backup files in $sensor_dir"
                fi
            fi
        done
    else
        success "Cache size is within limits (${cache_size}MB / ${MAX_CACHE_SIZE_MB}MB)"
    fi
    
    # Also clean memory cache
    if [ -d "memory/sensor_data" ]; then
        local sensor_data_size=$(du -sm memory/sensor_data | cut -f1)
        if [ "$sensor_data_size" -gt "100" ]; then  # 100MB limit for sensor data
            warning "Sensor data directory exceeds 100MB (current: ${sensor_data_size}MB). Cleaning..."
            find memory/sensor_data -type f -mtime +1 -delete
        fi
    fi
}

# Backup current config files
backup_config() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="config/backups"
    
    run_cmd "mkdir -p $backup_dir" "Creating config backup directory..."
    
    if [ -f "config/config.yaml" ]; then
        run_cmd "cp config/config.yaml $backup_dir/config_${timestamp}.yaml" "Backing up config.yaml..."
    fi
    
    # Keep only the most recent MAX_BACKUP_FILES config backups
    local backup_count=$(find "$backup_dir" -name "config_*.yaml" | wc -l)
    if [ "$backup_count" -gt "$MAX_BACKUP_FILES" ]; then
        find "$backup_dir" -name "config_*.yaml" | sort | head -n -"$MAX_BACKUP_FILES" | xargs rm -f
        success "Cleaned old config backups"
    fi
}

# Initialize or reset screen sensor cache
initialize_screen_cache() {
    info "Initializing screen sensor cache..."
    
    # Create screen cache directory if it doesn't exist
    mkdir -p cache/screen_sensor
    
    # Create detailed screen cache template
    cat > cache/screen_sensor/last_screen.json << EOF
{
  "timestamp": $(date +%s),
  "text": "# SensAI Agent-Based WebSocket Server\n\nThis is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses.\nThe server uses memory to store and retrieve context about the user's environment.\n\n## Features\n\n- Semantic search with TF-IDF vectorization\n- Specialized perception query handling\n- Context-aware responses from local LLM\n- Memory system integration\n\n## Current Status\n\nThe system is running with all necessary components initialized.",
  "screen_text": "# SensAI Agent-Based WebSocket Server\n\nThis is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses.\nThe server uses memory to store and retrieve context about the user's environment.\n\n## Features\n\n- Semantic search with TF-IDF vectorization\n- Specialized perception query handling\n- Context-aware responses from local LLM\n- Memory system integration\n\n## Current Status\n\nThe system is running with all necessary components initialized.",
  "window": "Terminal",
  "active_window": "Terminal",
  "has_images": false,
  "has_videos": false
}
EOF
    
    success "Initialized screen cache file with detailed content"
    
    # Create screen cache file for search
    if [ ! -f "cache/screen_sensor/screen_cache.json" ]; then
        cat > cache/screen_sensor/screen_cache.json << EOF
{
  "entries": [
    {
      "timestamp": $(date +%s),
      "text": "SensAI Agent-Based WebSocket Server",
      "window": "Terminal"
    }
  ]
}
EOF
        success "Initialized screen cache entries file"
    fi
}

# Initialize or reset process sensor cache
initialize_process_cache() {
    info "Initializing process sensor cache..."
    
    # Create process cache directory if it doesn't exist
    mkdir -p cache/process_sensor
    
    # Create process cache with more detailed information
    cat > cache/process_sensor/process_cache.json << EOF
{
  "timestamp": $(date +%s),
  "processes": [
    {
      "name": "bash",
      "pid": $$,
      "cpu": 0.0,
      "memory": 0.0
    },
    {
      "name": "Terminal",
      "pid": 1,
      "cpu": 0.0,
      "memory": 0.0
    }
  ],
  "window_history": [
    {
      "timestamp": $(date +%s),
      "window": "Terminal",
      "app": "Terminal"
    }
  ],
  "active_window": "Terminal",
  "active_app": "Terminal"
}
EOF
    
    success "Initialized process cache file with detailed content"
}

# Initialize file sensor cache
initialize_file_cache() {
    info "Initializing file sensor cache..."
    
    # Create file cache directory if it doesn't exist
    mkdir -p cache/file_sensor
    
    # Create file cache
    cat > cache/file_sensor/last_file.json << EOF
{
  "timestamp": $(date +%s),
  "files": [
    "agent_based_llm_ws.py",
    "run_agent_based_llm.sh",
    "connect_sensors.py",
    "test_perception_query.py"
  ],
  "current_file": {
    "name": "run_agent_based_llm.sh",
    "path": "$(pwd)/run_agent_based_llm.sh",
    "type": "text"
  }
}
EOF
    
    success "Initialized file cache file"
}

# Initialize memory state for perception queries
initialize_memory_state() {
    info "Initializing memory state..."
    
    # Create memory state directory
    mkdir -p memory
    
    # Create memory state file with screen content
    cat > memory/memory_state.json << EOF
{
  "short_term": [],
  "long_term": [],
  "context": {
    "sensor_data": {
      "screen": {
        "$(date +%Y-%m-%dT%H:%M:%S).000Z": {
          "data": {
            "text": "# SensAI Agent-Based WebSocket Server\n\nThis is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses.\nThe server uses memory to store and retrieve context about the user's environment.\n\n## Features\n\n- Semantic search with TF-IDF vectorization\n- Specialized perception query handling\n- Context-aware responses from local LLM\n- Memory system integration\n\n## Current Status\n\nThe system is running with all necessary components initialized.",
            "screen_content": "# SensAI Agent-Based WebSocket Server\n\nThis is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses.\nThe server uses memory to store and retrieve context about the user's environment.\n\n## Features\n\n- Semantic search with TF-IDF vectorization\n- Specialized perception query handling\n- Context-aware responses from local LLM\n- Memory system integration\n\n## Current Status\n\nThe system is running with all necessary components initialized.",
            "window": "Terminal",
            "active_window": "Terminal"
          },
          "timestamp": "$(date +%Y-%m-%dT%H:%M:%S).000Z"
        }
      },
      "process": {
        "$(date +%Y-%m-%dT%H:%M:%S).000Z": {
          "data": {
            "active_window": "Terminal",
            "active_app": "Terminal",
            "active_apps": ["Terminal", "bash", "python"]
          },
          "timestamp": "$(date +%Y-%m-%dT%H:%M:%S).000Z"
        }
      }
    },
    "last_update": "$(date +%Y-%m-%dT%H:%M:%S).000Z"
  }
}
EOF
    
    success "Initialized memory state with screen and process data"
    
    # Create memory context file
    cat > memory/last_context.json << EOF
{
  "timestamp": "$(date +%Y-%m-%dT%H:%M:%S).000Z",
  "screen_content": "# SensAI Agent-Based WebSocket Server\n\nThis is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses.\nThe server uses memory to store and retrieve context about the user's environment.",
  "window": "Terminal",
  "active_apps": ["Terminal", "bash", "python"]
}
EOF
    
    success "Initialized memory context file"
}

# Ensure Python dependencies
check_python_dependencies() {
    info "Checking Python dependencies..."
    
    # List of required packages
    local required_packages=(
        "websockets"
        "scikit-learn"
        "numpy"
        "aiohttp"
        "psutil"
    )
    
    # Check each package
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" &>/dev/null; then
            warning "Package '$package' is not installed. Installing..."
            pip3 install $package || {
                error "Failed to install $package. Please install it manually."
                return 1
            }
            success "Installed $package"
        fi
    done
    
    success "All required Python packages are installed"
    return 0
}

# Kill any existing processes
kill_existing_processes() {
    info "Checking for existing processes..."
    
    # Kill any process using port 8765
    if lsof -ti:8765 &>/dev/null; then
        run_cmd "lsof -ti:8765 | xargs kill -9" "Killing existing process on port 8765..."
    fi
    
    # Kill agent server if running by PID
    if [ -f "pids/agent_based_llm_ws.pid" ]; then
        PID=$(cat pids/agent_based_llm_ws.pid)
        if ps -p $PID &>/dev/null; then
            run_cmd "kill -9 $PID" "Killing existing agent-based server process: $PID"
        fi
        rm -f pids/agent_based_llm_ws.pid
    fi
    
    # Kill any sensors that might be running
    for pid_file in pids/*_sensor.pid pids/connect_sensors.pid; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file")
            if ps -p $PID &>/dev/null; then
                run_cmd "kill -9 $PID" "Killing existing sensor process: $PID (from $pid_file)"
            fi
            rm -f "$pid_file"
        fi
    done
    
    success "All existing processes have been checked and stopped if necessary"
}

# Initialize all sensor data
initialize_sensors() {
    info "Initializing all sensor data..."
    
    # Initialize cache files
    initialize_screen_cache
    initialize_process_cache
    initialize_file_cache
    
    # Initialize memory state for perception queries
    initialize_memory_state
    
    success "All sensor data initialized successfully"
}

# Run sensor connector
run_sensors() {
    info "Starting sensor connector..."
    
    # First run a single connection to update memory immediately
    python3 connect_sensors.py --verify
    
    # Then start the continuous sensor connector
    python3 connect_sensors.py --loop --interval 10 > logs/sensors.log 2>&1 &
    SENSOR_PID=$!
    echo $SENSOR_PID > pids/connect_sensors.pid
    
    # Make sure it's running
    sleep 1
    if ps -p $SENSOR_PID &>/dev/null; then
        success "Sensor connector is running with PID: $SENSOR_PID"
    else
        error "Sensor connector failed to start. Check logs/sensors.log for details."
        cat logs/sensors.log
    fi
}

# Monitor the server and sensors
start_monitoring() {
    info "Setting up system monitoring..."
    
    # Create a monitoring script
    cat > monitor_agent_system.sh << EOF
#!/bin/bash

# Monitor the agent-based system
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking system health..."
    
    # Check if server is running
    if [ -f "pids/agent_based_llm_ws.pid" ]; then
        SERVER_PID=\$(cat pids/agent_based_llm_ws.pid)
        if ps -p \$SERVER_PID > /dev/null; then
            echo "✅ Server is running (PID: \$SERVER_PID)"
        else
            echo "❌ Server process not found despite PID file existing"
        fi
    else
        echo "❌ Server PID file not found"
    fi
    
    # Check if sensor connector is running
    if [ -f "pids/connect_sensors.pid" ]; then
        SENSOR_PID=\$(cat pids/connect_sensors.pid)
        if ps -p \$SENSOR_PID > /dev/null; then
            echo "✅ Sensor connector is running (PID: \$SENSOR_PID)"
        else
            echo "❌ Sensor connector process not found despite PID file existing"
        fi
    else
        echo "❌ Sensor connector PID file not found"
    fi
    
    # Check memory usage
    MEM_USAGE=\$(ps -o rss= -p \$SERVER_PID | awk '{print \$1/1024 " MB"}')
    echo "📊 Server memory usage: \$MEM_USAGE"
    
    # Check for issues in logs
    ERROR_COUNT=\$(grep -c "ERROR" logs/agent_based_llm_ws.log | tail -100)
    echo "📋 Recent errors in log: \$ERROR_COUNT"
    
    echo "---------------------------------------------------"
    sleep 60
done
EOF
    
    chmod +x monitor_agent_system.sh
    
    # Run in background
    ./monitor_agent_system.sh > logs/system_monitor.log 2>&1 &
    MONITOR_PID=$!
    echo $MONITOR_PID > pids/system_monitor.pid
    
    success "System monitoring started (PID: $MONITOR_PID)"
}

# Main function
main() {
    echo -e "\n${BOLD}${BLUE}=== AGENT-BASED LLM WEBSOCKET SERVER STARTUP ===${NC}\n"
    
    # Check system requirements
    info "Checking system requirements..."
    
    # Verify Python is installed
    if ! command -v python3 &>/dev/null; then
        error "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    # Verify Ollama is running
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        warning "Ollama service does not appear to be running on port 11434."
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        success "Ollama service is running"
    fi
    
    # Check Python dependencies
    check_python_dependencies || {
        warning "Some Python dependencies could not be installed. Proceeding anyway..."
    }
    
    # Ensure directories exist
    ensure_directories
    
    # Check disk space
    check_disk_space "." $MIN_DISK_SPACE_PERCENT || {
        warning "Proceeding despite low disk space..."
    }
    
    # Clean logs and cache
    clean_logs
    clean_cache
    
    # Backup configurations
    backup_config
    
    # Kill any existing processes
    kill_existing_processes
    
    # Initialize all sensor data
    initialize_sensors
    
    # Start sensor connector to run in the background
    run_sensors
    
    # Wait a moment for sensors to initialize
    info "Waiting for sensors to initialize..."
    sleep 3
    
    # Start the main server
    info "Starting agent-based LLM WebSocket server..."
    
    # Clear any existing log file to make debugging easier
    : > logs/agent_based_llm_ws.log
    
    # Start the server with proper Python path
    python3 agent_based_llm_ws.py > logs/agent_based_llm_ws.log 2>&1 &
    SERVER_PID=$!
    
    # Save the PID
    echo $SERVER_PID > pids/agent_based_llm_ws.pid
    success "Server started with PID: $SERVER_PID"
    info "WebSocket server should be running on ws://localhost:8765"
    
    # Check that server is running after a brief delay
    info "Waiting for server to fully initialize (20 seconds)..."
    for i in {1..20}; do
        echo -n "."
        sleep 1
        
        # Check log file every 5 seconds for server startup confirmation
        if [ $((i % 5)) -eq 0 ]; then
            if grep -q "WebSocket server started on" logs/agent_based_llm_ws.log; then
                echo ""
                success "Server initialization confirmed in logs!"
                break
            fi
        fi
    done
    echo ""
    
    # Display last few log lines to help debug
    info "Recent server log entries:"
    tail -10 logs/agent_based_llm_ws.log
    
    # Check server connection
    if ps -p $SERVER_PID &>/dev/null; then
        # Wait until the server is actually accepting connections
        info "Verifying server connection..."
        MAX_RETRIES=8
        RETRY_COUNT=0
        SUCCESS=false
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
            # Try both localhost and 127.0.0.1
            if nc -z localhost 8765 &>/dev/null || nc -z 127.0.0.1 8765 &>/dev/null; then
                success "Server is accepting connections on port 8765!"
                SUCCESS=true
                
                # Additional verification: send a test message
                info "Sending test message to verify server is responding..."
                
                # Wait a moment to ensure server is fully ready
                sleep 3
                
                # Create a simple Python script to test connection
                cat > test_connection.py << EOF
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_connection():
    try:
        async with websockets.connect("ws://127.0.0.1:8765", ping_interval=None, close_timeout=5) as websocket:
            print("Connected to server")
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "timestamp": datetime.now().isoformat()
                }
            }))
            await asyncio.sleep(1)
            print("Test message sent successfully")
            sys.exit(0)
    except Exception as e:
        print(f"Connection test failed: {e}")
        sys.exit(1)

asyncio.run(test_connection())
EOF
                
                # Run the test
                python3 test_connection.py
                if [ $? -eq 0 ]; then
                    success "Server is responsive!"
                else
                    warning "Server did not respond to test message, but socket is open. Continuing..."
                fi
                
                # Clean up test script
                rm test_connection.py
            else
                RETRY_COUNT=$((RETRY_COUNT + 1))
                if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                    warning "Server not accepting connections yet, retrying in 5 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
                    sleep 5
                fi
            fi
        done
        
        if [ "$SUCCESS" = false ]; then
            warning "Server may not be accepting connections yet, but it's running. Continuing..."
            warning "This could cause issues with sensor connections."
            info "Check logs/agent_based_llm_ws.log for more information."
        fi
        
        # Start system monitoring
        start_monitoring
        
        # Display helpful information
        cat << EOF

${BOLD}${GREEN}Server started successfully!${NC}
${BLUE}---------------------------------------${NC}
Server URL:     ${BOLD}ws://localhost:8765${NC}
Server PID:     ${BOLD}$SERVER_PID${NC}
Sensor PID:     ${BOLD}$SENSOR_PID${NC}
Monitor logs:   ${BOLD}tail -f logs/agent_based_llm_ws.log${NC}
Stop server:    ${BOLD}./stop_agent_system.sh${NC}

To test perception queries:
${BOLD}python3 test_perception_query.py${NC}
${BLUE}---------------------------------------${NC}

EOF

        # Create a stop script for convenience
        cat > stop_agent_system.sh << EOF
#!/bin/bash

# Stop the agent-based system
echo "Stopping agent-based LLM system..."

# Kill server
if [ -f "pids/agent_based_llm_ws.pid" ]; then
    kill -9 \$(cat pids/agent_based_llm_ws.pid) 2>/dev/null
    rm pids/agent_based_llm_ws.pid
    echo "✅ Server stopped"
fi

# Kill sensor connector
if [ -f "pids/connect_sensors.pid" ]; then
    kill -9 \$(cat pids/connect_sensors.pid) 2>/dev/null
    rm pids/connect_sensors.pid
    echo "✅ Sensor connector stopped"
fi

# Kill monitor
if [ -f "pids/system_monitor.pid" ]; then
    kill -9 \$(cat pids/system_monitor.pid) 2>/dev/null
    rm pids/system_monitor.pid
    echo "✅ System monitor stopped"
fi

echo "All components stopped successfully."
EOF
        chmod +x stop_agent_system.sh
        
        # Run initial perception test to verify everything is working
        info "Running initial perception query test..."
        python3 test_perception_query.py --type perception
        
    else
        error "Server failed to start. Check logs/agent_based_llm_ws.log for errors."
        cat logs/agent_based_llm_ws.log
    fi
}

# Run the main function
main

exit 0