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

# Function to compare version numbers
version_compare() {
    local version1=$1
    local version2=$2
    local IFS=.
    local i ver1=($version1) ver2=($version2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
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

# Function to check if a process is running
check_process() {
    if [ -z "$1" ]; then
        return 1
    fi
    ps -p $1 > /dev/null 2>&1
}

# Function to check process logs for errors
check_process_logs() {
    local component=$1
    local log_file="logs/${component}.log"
    if [ -f "$log_file" ]; then
        if grep -i "error\|exception\|failed" "$log_file" > /dev/null; then
            return 1
        fi
    fi
    return 0
}

# Create necessary directories
mkdir -p logs
mkdir -p static/js
mkdir -p templates

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log "Detected Python version: $python_version" "$YELLOW"

version_compare "$python_version" "3.8"
if [ $? -eq 2 ]; then
    log "Error: Python 3.8 or higher is required" "$RED"
    exit 1
fi

# Check required Python modules
log "Checking required Python modules..."
required_modules=(
    "flask"
    "psutil"
    "watchdog"
    "numpy"
    "torch"
    "pandas"
    "scipy"
    "sklearn"
)

for module in "${required_modules[@]}"; do
    log "Checking $module..."
    check_python_module $module
done

# Clean up any existing processes
log "Cleaning up any existing processes..."
pkill -f "python.*sensor"
pkill -f "python.*model"
pkill -f "python.*main"
sleep 2

# Initialize environment variables
export PYTHONPATH=$(pwd)
export FLASK_APP=app.py
export FLASK_ENV=development

# Start components with proper error handling
start_component() {
    local component=$1
    local script=$2
    local logfile="logs/${component}.log"
    
    log "Starting ${component}..."
    python3 "$script" > "$logfile" 2>&1 &
    local pid=$!
    
    # Wait for initialization
    local count=0
    while [ $count -lt 10 ]; do
        sleep 1
        if ! check_process $pid; then
            log "Failed to start ${component}" "$RED"
            return 1
        fi
        if grep -q "initialized" "$logfile" 2>/dev/null; then
            log "${component} started successfully" "$GREEN"
            echo "$component:$pid" >> .running_pids
            return 0
        fi
        if check_process_logs "$component"; then
            count=$((count + 1))
        else
            log "Error detected in ${component} logs" "$RED"
            kill $pid 2>/dev/null
            return 1
        fi
    done
    
    log "Timeout waiting for ${component} to initialize" "$YELLOW"
    return 0
}

# Start components in sequence
components=(
    "ai_sensor:ai_sensor_main.py"
    "file_sensor:sensors/file_sensor_main.py"
    "process_sensor:sensors/process_sensor_main.py"
    "llm_model:llm/model_main.py"
    "main:main.py"
)

# Clear any existing PID file
> .running_pids

for comp in "${components[@]}"; do
    IFS=':' read -r name script <<< "$comp"
    if start_component "$name" "$script"; then
        sleep 2  # Give each component time to initialize
    else
        log "Failed to start $name, stopping all components..." "$RED"
        while read -r line; do
            IFS=':' read -r comp_name pid <<< "$line"
            kill $pid 2>/dev/null
        done < .running_pids
        exit 1
    fi
done

log "System is running. PIDs saved to .running_pids" "$GREEN"
log "View logs with: tail -f logs/*.log"
log "Stop system with: ./stop_simple.sh"

# Start log viewer in a new terminal window
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && tail -f logs/*.log"'

# Trap Ctrl+C
trap 'while read -r line; do IFS=":" read -r comp_name pid <<< "$line"; kill $pid 2>/dev/null; done < .running_pids; exit' INT

# Monitor processes
while true; do
    all_running=true
    while read -r line; do
        IFS=':' read -r name pid <<< "$line"
        if ! check_process $pid; then
            log "Process $name (PID: $pid) died unexpectedly" "$RED"
            all_running=false
            break
        fi
        if ! check_process_logs "$name"; then
            log "Errors detected in $name logs" "$RED"
            all_running=false
            break
        fi
    done < .running_pids
    
    if ! $all_running; then
        log "One or more components failed, stopping system..." "$RED"
        while read -r line; do
            IFS=':' read -r comp_name pid <<< "$line"
            kill $pid 2>/dev/null
        done < .running_pids
        exit 1
    fi
    
    sleep 5
done 