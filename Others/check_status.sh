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

# Function to check if tmux session exists
check_session() {
    tmux has-session -t local_assistant 2>/dev/null
}

# Function to check component status
check_component() {
    local pane=$1
    local name=$2
    local log_file="logs/${3}.log"
    
    # Check if process is running
    if tmux capture-pane -t local_assistant:0.$pane -p | grep -q "failed to start"; then
        log "$name is not running" "$RED"
        return 1
    fi
    
    # Check log file for errors
    if [ -f "$log_file" ]; then
        local error_count=$(grep -c "ERROR" "$log_file")
        local warning_count=$(grep -c "WARNING" "$log_file")
        
        if [ $error_count -gt 0 ]; then
            log "$name has $error_count errors" "$RED"
            log "Last error: $(tail -n 1 <(grep "ERROR" "$log_file"))" "$RED"
        elif [ $warning_count -gt 0 ]; then
            log "$name has $warning_count warnings" "$YELLOW"
        else
            log "$name is running normally" "$GREEN"
        fi
        
        # Check resource usage
        local pid=$(pgrep -f "python.*$3.py" | head -n 1)
        if [ ! -z "$pid" ]; then
            local cpu=$(ps -p $pid -o %cpu | tail -n 1)
            local mem=$(ps -p $pid -o %mem | tail -n 1)
            log "$name resource usage: CPU: $cpu%, Memory: $mem%" "$YELLOW"
        fi
    else
        log "$name log file not found" "$RED"
        return 1
    fi
}

# Check if session exists
if ! check_session; then
    log "Local Assistant is not running" "$RED"
    exit 1
fi

# Print header
log "=== Local Assistant Status ===" "$YELLOW"

# Check each component
check_component 0 "AI Sensor" "ai_sensor"
check_component 1 "File Sensor" "file_sensor"
check_component 2 "Process Sensor" "process_sensor"
check_component 3 "LLM Model" "llm_model"
check_component 4 "Main Application" "main"

# Check overall system health
log "\n=== System Health ===" "$YELLOW"

# Check disk space
disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -gt 90 ]; then
    log "Disk usage is critical: $disk_usage%" "$RED"
elif [ $disk_usage -gt 80 ]; then
    log "Disk usage is high: $disk_usage%" "$YELLOW"
else
    log "Disk usage is normal: $disk_usage%" "$GREEN"
fi

# Check memory usage
mem_usage=$(free | awk '/Mem:/ {printf("%.2f", $3/$2 * 100)}')
if [ $(echo "$mem_usage > 90" | bc) -eq 1 ]; then
    log "Memory usage is critical: $mem_usage%" "$RED"
elif [ $(echo "$mem_usage > 80" | bc) -eq 1 ]; then
    log "Memory usage is high: $mem_usage%" "$YELLOW"
else
    log "Memory usage is normal: $mem_usage%" "$GREEN"
fi

# Check CPU load
load_avg=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1)
if [ $(echo "$load_avg > 2" | bc) -eq 1 ]; then
    log "CPU load is high: $load_avg" "$RED"
elif [ $(echo "$load_avg > 1" | bc) -eq 1 ]; then
    log "CPU load is moderate: $load_avg" "$YELLOW"
else
    log "CPU load is normal: $load_avg" "$GREEN"
fi

# Check log sizes
log "\n=== Log Sizes ===" "$YELLOW"
for log_file in logs/*.log; do
    if [ -f "$log_file" ]; then
        size=$(du -h "$log_file" | cut -f1)
        log "$(basename "$log_file"): $size" "$NC"
    fi
done 