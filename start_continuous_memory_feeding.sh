#!/bin/bash

# Start Continuous Memory Feeding Service
# Keeps the memory system fed with real meaningful data

echo "🚀 STARTING CONTINUOUS MEMORY FEEDING SERVICE"
echo "=============================================="
echo "📊 Real-time sensor data feeding to memory system"
echo "🔄 Running in background with automatic restart"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs/continuous_feeding

# Function to start the feeder
start_feeder() {
    echo "⚡ Starting memory feeder..."
    python simple_continuous_memory_feeder.py >> logs/continuous_feeding/feeder.log 2>&1 &
    FEEDER_PID=$!
    echo $FEEDER_PID > pids/memory_feeder.pid
    echo "✅ Memory feeder started (PID: $FEEDER_PID)"
}

# Function to stop the feeder
stop_feeder() {
    if [ -f pids/memory_feeder.pid ]; then
        PID=$(cat pids/memory_feeder.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "🛑 Stopping memory feeder (PID: $PID)..."
            kill $PID
            rm -f pids/memory_feeder.pid
            echo "✅ Memory feeder stopped"
        else
            echo "⚠️ Memory feeder not running"
            rm -f pids/memory_feeder.pid
        fi
    else
        echo "⚠️ No memory feeder PID file found"
    fi
}

# Function to check status
check_status() {
    if [ -f pids/memory_feeder.pid ]; then
        PID=$(cat pids/memory_feeder.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "🟢 Memory feeder is running (PID: $PID)"
            
            # Check memory entries
            ENTRIES=$(python -c "import json; data=json.load(open('memory/memory/memory_state.json')); print(len(data.get('short_term', [])))" 2>/dev/null || echo "0")
            echo "📊 Memory entries: $ENTRIES"
            
            # Check latest activity
            LATEST=$(python -c "import json; data=json.load(open('memory/memory/memory_state.json')); entries=data.get('short_term', []); print(entries[-1].get('user_activity', {}).get('detected_activity', 'unknown') + ' in ' + entries[-1].get('application_context', {}).get('active_application', 'unknown') if entries else 'no entries')" 2>/dev/null || echo "unknown")
            echo "🎯 Latest activity: $LATEST"
            
            return 0
        else
            echo "🔴 Memory feeder not running"
            rm -f pids/memory_feeder.pid
            return 1
        fi
    else
        echo "🔴 Memory feeder not running"
        return 1
    fi
}

# Function to restart the feeder
restart_feeder() {
    echo "🔄 Restarting memory feeder..."
    stop_feeder
    sleep 2
    start_feeder
}

# Handle command line arguments
case "$1" in
    start)
        start_feeder
        ;;
    stop)
        stop_feeder
        ;;
    restart)
        restart_feeder
        ;;
    status)
        check_status
        ;;
    monitor)
        echo "📊 CONTINUOUS MEMORY MONITORING"
        echo "================================"
        echo "🔄 Monitoring memory feeding every 30 seconds"
        echo "🛑 Press Ctrl+C to stop monitoring"
        echo ""
        
        while true; do
            echo "$(date '+%H:%M:%S') - $(check_status)"
            sleep 30
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor}"
        echo ""
        echo "Commands:"
        echo "  start    - Start continuous memory feeding"
        echo "  stop     - Stop memory feeding"
        echo "  restart  - Restart memory feeding"
        echo "  status   - Check feeding status"
        echo "  monitor  - Monitor feeding continuously"
        echo ""
        echo "Examples:"
        echo "  $0 start     # Start feeding in background"
        echo "  $0 status    # Check if feeding is running"
        echo "  $0 monitor   # Watch real-time feeding"
        exit 1
        ;;
esac