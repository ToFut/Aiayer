#!/bin/bash

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

printf "${BOLD}${RED}⚠️ STOPPING SENSAI COMPLETE SYSTEM...${RESET}\n"

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            printf "${YELLOW}→ Stopping %s (PID: %d)${RESET}\n" "$COMPONENT" "$PID"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
printf "→ Cleaning up remaining processes...${RESET}\n"
pkill -f "neural_ui_detector" 2>/dev/null || true
pkill -f "start_neural_ui_detector" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
pkill -f "start_direct_automation" 2>/dev/null || true
pkill -f "neural_ui_do_button_handler" 2>/dev/null || true
pkill -f "start_neural_ui_handler" 2>/dev/null || true
pkill -f "enhanced_enterprise_backend" 2>/dev/null || true
pkill -f "enterprise_backend_8767" 2>/dev/null || true
pkill -f "simple_backend_server" 2>/dev/null || true
pkill -f "smart_memory_feeder" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true
pkill -f "simple_process_sensor" 2>/dev/null || true
pkill -f "total_screen_analyzer" 2>/dev/null || true
pkill -f "fixed_bridge_server" 2>/dev/null || true
pkill -f "fixed_bridge_server_ports" 2>/dev/null || true
pkill -f "python3 -m http.server" 2>/dev/null || true
pkill -f "llm_warmup_manager" 2>/dev/null || true

# Clean up ports
printf "→ Freeing used ports...${RESET}\n"
for PORT in 8000 8765 8766 8767 8768; do
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
done

printf "${GREEN}✅ SENSAI COMPLETE SYSTEM STOPPED${RESET}\n"
