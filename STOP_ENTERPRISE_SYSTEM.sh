#!/bin/bash

# Stop Enterprise System Script
# Professional shutdown with validation cleanup

echo "🛑 STOPPING ENTERPRISE SENSAI SYSTEM"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Set working directory
cd "$(dirname "$0")"

# Read system info if available
if [ -f .enterprise_system_info ]; then
    source .enterprise_system_info
    log_info "Found enterprise system info from: $ENTERPRISE_SYSTEM_STARTED"
fi

# Stop enterprise backend
log_info "Stopping Enhanced Enterprise Backend..."
if [ -f pids/enterprise_backend.pid ]; then
    BACKEND_PID=$(cat pids/enterprise_backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        sleep 3
        if ps -p $BACKEND_PID > /dev/null; then
            kill -9 $BACKEND_PID
            log_warning "Force killed enterprise backend"
        else
            log_success "Enterprise backend stopped gracefully"
        fi
    fi
    rm -f pids/enterprise_backend.pid
fi

# Kill any remaining enterprise processes
log_info "Cleaning up enterprise processes..."
pkill -f "enhanced_enterprise_backend.py" 2>/dev/null
pkill -f "enterprise_agent_reflection.py" 2>/dev/null
pkill -f "specialized_agents.py" 2>/dev/null
pkill -f "deep_dive_validator.py" 2>/dev/null

# Clean up enterprise logs and cache
log_info "Archiving enterprise logs..."
if [ -d logs/enterprise_reflection ]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p logs/archive
    tar -czf logs/archive/enterprise_logs_$timestamp.tar.gz logs/enterprise_reflection/
    rm -rf logs/enterprise_reflection/*
    log_success "Enterprise logs archived to logs/archive/enterprise_logs_$timestamp.tar.gz"
fi

# Clean up validation evidence
if [ -d cache/validation_evidence ]; then
    rm -rf cache/validation_evidence/*
    log_info "Validation evidence cache cleared"
fi

# Clean up temporary files
if [ -d tmp/professional_screenshots ]; then
    rm -rf tmp/professional_screenshots/*
    log_info "Professional screenshots cache cleared"
fi

# Remove system info
rm -f .enterprise_system_info

log_success "Enterprise SensAI System stopped successfully"
echo "Professional agent self-reflection and collaboration disabled"