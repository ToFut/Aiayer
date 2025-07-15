#!/bin/bash
echo "🛑 Stopping Lightweight SensAI System..."

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
pkill -f lightweight_backend 2>/dev/null || true
pkill -f lightweight_process_sensor 2>/dev/null || true
pkill -f lightweight_screen_sensor 2>/dev/null || true
pkill -f direct_coordinate_automation 2>/dev/null || true

# Clean up ports
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true

echo "✅ Lightweight SensAI System stopped"
