#!/bin/bash
echo " Stopping Complete Enhanced System with Neural UI Detector and DO Button Fix (All Components)..."

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            echo "Stopping $COMPONENT (PID: $PID)"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f real_llm_backend 2>/dev/null || true
pkill -f enhanced_brain_router 2>/dev/null || true
pkill -f contextual 2>/dev/null || true
pkill -f llm_warmup_manager 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true  
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration_service 2>/dev/null || true
pkill -f smart_memory_feeder 2>/dev/null || true
pkill -f conscious_memory 2>/dev/null || true
pkill -f semantic_search 2>/dev/null || true
pkill -f neural_ui_detector_server 2>/dev/null || true
pkill -f direct_coordinate_automation 2>/dev/null || true
pkill -f memory_aware_suggestion_monitor 2>/dev/null || true
pkill -f fix_do_button_connection_bridge 2>/dev/null || true
pkill -f ultimate_do_button_server 2>/dev/null || true

# Clean up ports to ensure they're available next time
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8766 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
lsof -ti:8768 | xargs kill -9 2>/dev/null || true

echo " Complete Enhanced System with Neural UI Detector stopped"
echo " All neural UI detection, performance optimizations, TeamViewer capabilities, and DO button fix stopped"
