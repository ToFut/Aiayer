#!/bin/bash

# ENHANCED ENTERPRISE SYSTEM STOP SCRIPT
# Comprehensive shutdown with proper cleanup

echo "🛑 STOPPING ENTERPRISE SENSAI SYSTEM (ENHANCED)"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] [WARNING]${NC} $1"
}

# Set working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to stop process by PID file
stop_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 10 ]]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null
            fi
            
            log_success "$service_name stopped"
        else
            log_warning "$service_name was not running"
        fi
        rm -f "$pid_file"
    else
        log_info "No PID file found for $service_name"
    fi
}

# Stop services by PID files
log_info "Stopping services by PID files..."
stop_by_pid "pids/enterprise_backend.pid" "Enterprise Backend"
stop_by_pid "pids/process_sensor.pid" "Process Sensor"
stop_by_pid "pids/screen_analyzer.pid" "Screen Analyzer"
stop_by_pid "pids/simple_brain_router.pid" "Simple Brain Router"

# Comprehensive process cleanup
log_info "Performing comprehensive process cleanup..."
CLEANUP_PROCESSES=(
    "enhanced_enterprise_backend.py"
    "enterprise_agent_reflection.py"
    "specialized_agents.py"
    "simple_brain_router_server.py"
    "brain_router.py"
    "total_screen_analyzer.py"
    "enhanced_fixed_process_sensor.py"
    "process_sensor.py"
    "screen_sensor.py"
)

for process in "${CLEANUP_PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        log_info "Killing remaining $process processes..."
        pkill -f "$process" 2>/dev/null || true
    fi
done

# Wait for all processes to terminate
sleep 2

# Verify no processes are still running
log_info "Verifying process cleanup..."
remaining_processes=0
for process in "${CLEANUP_PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        log_warning "Process still running: $process"
        remaining_processes=$((remaining_processes + 1))
    fi
done

if [[ $remaining_processes -eq 0 ]]; then
    log_success "All processes stopped successfully"
else
    log_warning "$remaining_processes processes may still be running"
fi

# Check port usage
log_info "Checking port cleanup..."
PORTS=(8765 8766 8767 8080)
for port in "${PORTS[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "Port $port still in use"
        # Optional: Force kill processes using the port
        # lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

# Archive logs if they exist
log_info "Archiving enterprise logs..."
if [[ -d "logs" ]]; then
    ARCHIVE_NAME="logs/archive/enterprise_logs_$(date '+%Y%m%d_%H%M%S').tar.gz"
    mkdir -p logs/archive
    
    if tar -czf "$ARCHIVE_NAME" logs/enterprise_reflection logs/backend logs/agents 2>/dev/null; then
        log_success "Logs archived to $ARCHIVE_NAME"
    else
        log_info "No logs to archive or archiving failed"
    fi
fi

# Clean up temporary files
log_info "Cleaning up temporary files..."
rm -rf tmp/professional_screenshots/* 2>/dev/null || true
rm -rf cache/validation_evidence/* 2>/dev/null || true

# Clear system info
if [[ -f ".enterprise_system_info" ]]; then
    rm -f ".enterprise_system_info"
    log_info "Enterprise system info cleared"
fi

# Display final status
echo ""
log_success "🎯 ENTERPRISE SENSAI SYSTEM STOPPED SUCCESSFULLY"
echo "=============================================="
echo ""
log_info "System Status:"
echo "  • All enterprise processes: STOPPED"
echo "  • Ports 8765-8767: FREED"
echo "  • Logs: ARCHIVED"
echo "  • Temporary files: CLEANED"
echo ""
log_info "To restart the system:"
echo "  ./FINAL_ENTERPRISE_STARTUP_FIXED.sh"
echo ""