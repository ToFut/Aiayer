#!/bin/bash

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${RED}⚠️ STOPPING SENSAI MASTER SYSTEM...${RESET}"

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}→ Stopping $COMPONENT (PID: $PID)${RESET}"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
echo -e "${YELLOW}→ Cleaning up remaining processes...${RESET}"
pkill -f "neural_ui_detector_server" 2>/dev/null || true
pkill -f "simple_neural_ui_detector" 2>/dev/null || true
pkill -f "neural_ui_do_button_handler" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
pkill -f "enhanced_enterprise_backend" 2>/dev/null || true
pkill -f "simple_backend_server" 2>/dev/null || true
pkill -f "smart_memory_feeder" 2>/dev/null || true
pkill -f "enhanced_fixed_process_sensor" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true
pkill -f "total_screen_analyzer" 2>/dev/null || true
pkill -f "memory_aware_suggestion_monitor" 2>/dev/null || true
pkill -f "fixed_bridge_server" 2>/dev/null || true
pkill -f "python3 -m http.server 8000" 2>/dev/null || true

# Clean up ports
echo -e "${YELLOW}→ Freeing used ports...${RESET}"
for PORT in 8000 8765 8766 8767 8768; do
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
done

echo -e "${GREEN}✅ SENSAI MASTER SYSTEM STOPPED${RESET}"
