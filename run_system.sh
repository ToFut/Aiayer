#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${2:-$NC}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        log "Error: $1 is not installed. Please install it first." "$RED"
        exit 1
    fi
}

# Function to check if a Python module exists
check_python_module() {
    python3 -c "import $1" 2>/dev/null
    if [ $? -ne 0 ]; then
        log "Error: Python module $1 is not installed. Installing..." "$YELLOW"
        pip install $1
        if [ $? -ne 0 ]; then
            log "Failed to install $1" "$RED"
            exit 1
        fi
    fi
}

# Function to check if tmux session already exists
check_session() {
    tmux has-session -t local_assistant 2>/dev/null
    if [ $? -eq 0 ]; then
        log "Error: local_assistant session already exists. Please stop it first:" "$RED"
        log "Run: ./stop_system.sh" "$YELLOW"
        exit 1
    fi
}

# Function to wait for component startup
wait_for_component() {
    local pane=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if tmux capture-pane -t local_assistant:0.$pane -p | grep -q "initialized"; then
            log "$name started successfully" "$GREEN"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log "$name failed to start" "$RED"
    return 1
}

# Check required commands
log "Checking required commands..."
check_command tmux
check_command python3
check_command pip

# Check required Python modules
log "Checking required Python modules..."
check_python_module psutil
check_python_module torch
check_python_module numpy
check_python_module pandas
check_python_module scipy
check_python_module sklearn

# Check for existing session
check_session

# Create log directory
mkdir -p logs

# Create a new tmux session
log "Creating tmux session..."
tmux new-session -d -s local_assistant

# Set window title
tmux rename-window -t local_assistant:0 'Local Assistant'

# Split the window into 5 panes
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v
tmux select-pane -t 2
tmux split-window -v

# Configure logging for each component
log "Starting components..."
tmux send-keys -t 0 "cd $(pwd) && python ai_sensor_main.py 2>&1 | tee logs/ai_sensor.log || echo 'AI Sensor failed to start'" C-m
tmux send-keys -t 1 "cd $(pwd) && python sensors/file_sensor_main.py 2>&1 | tee logs/file_sensor.log || echo 'File Sensor failed to start'" C-m
tmux send-keys -t 2 "cd $(pwd) && python sensors/process_sensor_main.py 2>&1 | tee logs/process_sensor.log || echo 'Process Sensor failed to start'" C-m
tmux send-keys -t 3 "cd $(pwd) && python llm/model_main.py 2>&1 | tee logs/llm_model.log || echo 'LLM Model failed to start'" C-m
tmux send-keys -t 4 "cd $(pwd) && PYTHONPATH=$(pwd) python main.py 2>&1 | tee logs/main.log || echo 'Main application failed to start'" C-m

# Wait for components to start with better detection
log "Waiting for components to initialize..."
for i in {1..30}; do
    all_started=true
    
    # Check each component's log for initialization message
    for component in "ai_sensor" "file_sensor" "process_sensor" "llm_model" "main"; do
        if ! grep -q "initialized" "logs/${component}.log" 2>/dev/null; then
            all_started=false
            break
        fi
    done
    
    if $all_started; then
        log "All components started successfully" "$GREEN"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log "Timeout waiting for components to start" "$RED"
        ./stop_system.sh
        exit 1
    fi
    
    sleep 1
    log "Waiting for components to initialize... ($i/30)" "$YELLOW"
done

# Set up monitoring
tmux new-window -t local_assistant:1 -n 'Monitor'
tmux send-keys -t local_assistant:1 "watch -n 1 'ps aux | grep python | grep -v grep'" C-m

# Set up log viewer
tmux new-window -t local_assistant:2 -n 'Logs'
tmux send-keys -t local_assistant:2 "tail -f logs/*.log" C-m

# Attach to the session
log "System started successfully" "$GREEN"
log "Use 'Ctrl+b n' to switch between windows:" "$YELLOW"
log "  - Window 0: Components" "$YELLOW"
log "  - Window 1: Process Monitor" "$YELLOW"
log "  - Window 2: Log Viewer" "$YELLOW"
log "Use 'Ctrl+b d' to detach from session" "$YELLOW"

tmux attach-session -t local_assistant

# Cleanup on exit
trap './stop_system.sh' EXIT 