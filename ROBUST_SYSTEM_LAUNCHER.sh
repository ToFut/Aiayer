#!/bin/bash

# SensAI Robust System Launcher - Deep Dive Restructure
# Comprehensive launch system with full error handling and recovery

echo "🚀 SensAI Enhanced Enterprise System - ROBUST LAUNCHER"
echo "================================================================="
echo "🎯 COMPLETE SYSTEM: Memory + Screen Capture + TeamViewer + Agent Mode"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Configuration
BACKEND_PORT=8767
MAX_STARTUP_TIME=30
HEALTH_CHECK_INTERVAL=5

# Create comprehensive logging
mkdir -p logs/{backend,memory,sensors,system}
mkdir -p pids
mkdir -p cache/{screen_sensor,process_sensor,ui_detection}

# Cleanup function
cleanup_system() {
    echo "🛑 Cleaning up existing processes..."
    
    # Kill by PID files first
    for pidfile in pids/*.pid; do
        if [ -f "$pidfile" ]; then
            PID=$(cat "$pidfile" 2>/dev/null)
            if [ ! -z "$PID" ] && ps -p $PID > /dev/null 2>&1; then
                echo "Stopping $(basename "$pidfile" .pid) (PID: $PID)"
                kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
                sleep 1
            fi
            rm -f "$pidfile"
        fi
    done
    
    # Kill by process name patterns
    pkill -f enhanced_enterprise_backend 2>/dev/null || true
    pkill -f process_sensor 2>/dev/null || true
    pkill -f total_screen_analyzer 2>/dev/null || true
    pkill -f memory_integration 2>/dev/null || true
    pkill -f smart_memory_feeder 2>/dev/null || true
    pkill -f llm_warmup_manager 2>/dev/null || true
    
    # Force kill port if needed
    lsof -ti :$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    sleep 3
    echo "✅ Cleanup completed"
}

# Health check function
check_component_health() {
    local component_name=$1
    local pid_file=$2
    local check_command=$3
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            if [ ! -z "$check_command" ]; then
                if eval "$check_command" > /dev/null 2>&1; then
                    echo "✅ $component_name is healthy (PID: $PID)"
                    return 0
                else
                    echo "⚠️  $component_name running but not responding (PID: $PID)"
                    return 1
                fi
            else
                echo "✅ $component_name is running (PID: $PID)"
                return 0
            fi
        else
            echo "❌ $component_name failed (PID: $PID not running)"
            return 1
        fi
    else
        echo "❌ $component_name not started (no PID file)"
        return 1
    fi
}

# Wait for service function
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_wait=$3
    local wait_time=0
    
    echo "⏳ Waiting for $service_name to start..."
    while [ $wait_time -lt $max_wait ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        sleep 2
        wait_time=$((wait_time + 2))
        echo "   Waiting... ${wait_time}s/${max_wait}s"
    done
    
    echo "❌ $service_name failed to start within ${max_wait}s"
    return 1
}

# Start component function
start_component() {
    local component_name=$1
    local start_command=$2
    local pid_file=$3
    local log_file=$4
    local health_check=$5
    
    echo "🚀 Starting $component_name..."
    
    # Start the component
    eval "$start_command > $log_file 2>&1 &"
    local PID=$!
    echo $PID > "$pid_file"
    
    # Wait a moment for startup
    sleep 3
    
    # Check if it's still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ $component_name started (PID: $PID)"
        
        # Optional health check
        if [ ! -z "$health_check" ]; then
            if wait_for_service "$component_name" "$health_check" 15; then
                return 0
            else
                echo "❌ $component_name failed health check"
                kill $PID 2>/dev/null || true
                rm -f "$pid_file"
                return 1
            fi
        fi
        return 0
    else
        echo "❌ $component_name failed to start"
        rm -f "$pid_file"
        echo "Last log entries:"
        tail -5 "$log_file" 2>/dev/null || echo "No logs available"
        return 1
    fi
}

# Main startup sequence
main() {
    echo "🔧 Starting robust system initialization..."
    
    # Step 1: Cleanup
    cleanup_system
    
    # Step 2: Check dependencies
    echo ""
    echo "🔍 Checking system dependencies..."
    
    # Check Ollama
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama LLM service is running"
        OLLAMA_OK=true
    else
        echo "❌ Ollama LLM service not running"
        echo "🔧 Please start Ollama: ollama serve"
        OLLAMA_OK=false
    fi
    
    # Check Python dependencies
    python3 -c "import websockets, asyncio, json" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Python WebSocket dependencies available"
        PYTHON_OK=true
    else
        echo "❌ Python dependencies missing"
        echo "🔧 Installing: pip3 install websockets"
        pip3 install websockets
        PYTHON_OK=true
    fi
    
    # Check PyAutoGUI for automation
    python3 -c "import pyautogui" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ PyAutoGUI automation available"
        AUTOMATION_OK=true
    else
        echo "❌ PyAutoGUI not available"
        echo "🔧 Installing: pip3 install pyautogui"
        pip3 install pyautogui
        AUTOMATION_OK=true
    fi
    
    # Step 3: Start core backend
    echo ""
    echo "🏢 Starting Enhanced Enterprise Backend..."
    if start_component "Enhanced Backend" \
       "python3 enhanced_enterprise_backend_with_context.py" \
       "pids/enhanced_enterprise_backend.pid" \
       "logs/backend/enhanced_enterprise_8767.log" \
       "curl -s http://localhost:8767 > /dev/null || python3 -c 'import websockets; import asyncio; asyncio.run(websockets.connect(\"ws://localhost:8767\"))' 2>/dev/null"; then
        
        BACKEND_OK=true
        echo "✅ Enhanced Backend is running on ws://localhost:8767"
        
        # Step 4: Start sensors
        echo ""
        echo "🔧 Starting sensor systems..."
        
        # Process Sensor
        if [ -f "sensors/enhanced_fixed_process_sensor.py" ]; then
            start_component "Process Sensor" \
               "python3 sensors/enhanced_fixed_process_sensor.py" \
               "pids/process_sensor.pid" \
               "logs/sensors/process_sensor.log"
        fi
        
        # Screen Analyzer
        if [ -f "sensors/total_screen_analyzer.py" ]; then
            start_component "Total Screen Analyzer" \
               "python3 sensors/total_screen_analyzer.py" \
               "pids/total_screen_analyzer.pid" \
               "logs/sensors/total_screen_analyzer.log"
        fi
        
        # Memory Integration
        if [ -f "memory/memory_integration_service.py" ]; then
            start_component "Memory Integration" \
               "python3 memory/memory_integration_service.py" \
               "pids/memory_integration.pid" \
               "logs/memory/integration_service.log"
        fi
        
        # Smart Memory Feeder
        if [ -f "smart_memory_feeder.py" ]; then
            start_component "Smart Memory Feeder" \
               "python3 smart_memory_feeder.py" \
               "pids/smart_memory_feeder.pid" \
               "logs/memory/smart_feeder.log"
        fi
        
    else
        echo "❌ Backend failed to start - cannot continue"
        BACKEND_OK=false
    fi
    
    # Step 5: System health check and status report
    echo ""
    echo "🔍 Final system health check..."
    RUNNING_COMPONENTS=0
    TOTAL_COMPONENTS=0
    
    # Check each component
    for component in enhanced_enterprise_backend process_sensor total_screen_analyzer memory_integration smart_memory_feeder; do
        TOTAL_COMPONENTS=$((TOTAL_COMPONENTS + 1))
        if check_component_health "$component" "pids/${component}.pid"; then
            RUNNING_COMPONENTS=$((RUNNING_COMPONENTS + 1))
        fi
    done
    
    # System status
    echo ""
    echo "📊 SYSTEM STATUS REPORT"
    echo "================================================================="
    echo "🏢 Enhanced Backend: $([ "$BACKEND_OK" = true ] && echo "✅ RUNNING" || echo "❌ FAILED")"
    echo "🤖 Ollama LLM: $([ "$OLLAMA_OK" = true ] && echo "✅ AVAILABLE" || echo "❌ UNAVAILABLE")"
    echo "🔧 Sensors Running: $RUNNING_COMPONENTS/$TOTAL_COMPONENTS"
    echo "🌐 WebSocket Endpoint: ws://localhost:8767"
    echo ""
    
    if [ "$BACKEND_OK" = true ]; then
        echo "🎯 ENHANCED CAPABILITIES ACTIVE:"
        echo "   ✅ Agent Mode - Real LLM automation planning"
        echo "   ✅ Ask Mode - Visual context + Memory integration"
        echo "   ✅ Suggest Mode - Context-aware suggestions"
        echo "   ✅ General Mode - Conversational AI with memory"
        echo "   🖥️  Screen Analysis - Real-time visual understanding"
        echo "   🧠 Memory System - Persistent context and learning"
        echo "   🎮 Input Control - Real PyAutoGUI automation"
        echo ""
        echo "🧪 Test System:"
        echo "   python3 test_spotify_agent_fix.py      # Test Agent Mode"
        echo "   python3 test_all_modes_final.py        # Test All Modes"
        echo "   python3 comprehensive_performance_test.py  # Performance Test"
        echo ""
        echo "📊 Monitor System:"
        echo "   tail -f logs/backend/enhanced_enterprise_8767.log"
        echo "   tail -f logs/sensors/process_sensor.log"
        echo "   tail -f logs/memory/integration_service.log"
        echo ""
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
        echo ""
        
        # Create or update stop script
        cat > STOP_ENHANCED_SYSTEM.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping SensAI Enhanced System..."

# Stop by PID files
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping $COMPONENT (PID: $PID)"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f process_sensor 2>/dev/null || true
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration 2>/dev/null || true
pkill -f smart_memory_feeder 2>/dev/null || true

# Clean up port
lsof -ti :8767 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "✅ SensAI Enhanced System stopped"
STOP_EOF
        chmod +x STOP_ENHANCED_SYSTEM.sh
        
        echo "✅ SYSTEM READY! Use the test commands above to verify functionality."
        
        # Show live logs
        echo ""
        echo "📊 Showing live backend logs (Ctrl+C to stop logs, system keeps running):"
        echo "----------------------------------------"
        tail -f logs/backend/enhanced_enterprise_8767.log 2>/dev/null | sed 's/^/[BACKEND] /' || {
            echo "System running in background - check logs manually if needed"
        }
        
    else
        echo "❌ SYSTEM STARTUP FAILED"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   1. Check Ollama: ollama serve"
        echo "   2. Check logs: tail -20 logs/backend/enhanced_enterprise_8767.log"
        echo "   3. Check dependencies: python3 -c 'import websockets, asyncio'"
        echo "   4. Try manual start: python3 enhanced_enterprise_backend_with_context.py"
        echo ""
        exit 1
    fi
}

# Trap signals for cleanup
trap 'echo ""; echo "🛑 Interrupted - cleaning up..."; cleanup_system; exit 1' INT TERM

# Run main function
main "$@"