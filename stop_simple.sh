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

# Check if PIDs file exists
if [ ! -f .running_pids ]; then
    log "No running processes found" "$YELLOW"
    exit 0
fi

# Read PIDs
PIDS=$(cat .running_pids)

# Stop each process
for pid in $PIDS; do
    if ps -p $pid > /dev/null 2>&1; then
        log "Stopping process $pid..." "$YELLOW"
        kill -TERM $pid 2>/dev/null
    fi
done

# Wait for processes to stop
sleep 2

# Force kill any remaining processes
for pid in $PIDS; do
    if ps -p $pid > /dev/null 2>&1; then
        log "Force stopping process $pid..." "$RED"
        kill -9 $pid 2>/dev/null
    fi
done

# Clean up PIDs file
rm -f .running_pids

# Kill any remaining Python processes from our components
pkill -f "python.*sensor"
pkill -f "python.*model"
pkill -f "python.*main"

log "All components stopped" "$GREEN" 