#!/bin/bash

# START_CONTEXTUAL_SYSTEM.sh
# Enhanced startup script for contextual AI system with semantic memory

echo "🚀 Starting Enhanced Contextual AI System..."
echo "==========================================="

# Create necessary directories
mkdir -p logs/backend
mkdir -p logs/brain_router
mkdir -p memory
mkdir -p pids

# Function to start service and track PID
start_service() {
    local name=$1
    local command=$2
    local pidfile=$3
    
    echo "🔄 Starting $name..."
    
    # Kill existing process if running
    if [ -f "$pidfile" ]; then
        local old_pid=$(cat "$pidfile")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "   Stopping existing $name (PID: $old_pid)"
            kill "$old_pid"
            sleep 2
        fi
        rm -f "$pidfile"
    fi
    
    # Start new process
    $command &
    local new_pid=$!
    echo $new_pid > "$pidfile"
    sleep 3
    
    # Check if process is still running
    if kill -0 "$new_pid" 2>/dev/null; then
        echo "   ✅ $name started successfully (PID: $new_pid)"
        return 0
    else
        echo "   ❌ Failed to start $name"
        rm -f "$pidfile"
        return 1
    fi
}

echo ""
echo "🧠 Starting Enhanced Brain Router with Contextual Memory..."
start_service "Enhanced Brain Router" "python3 enhanced_brain_router_with_context.py" "pids/brain_router_contextual.pid"

echo ""
echo "🏢 Starting Enhanced Enterprise Backend with Context..."
start_service "Enhanced Enterprise Backend" "python3 enhanced_enterprise_backend_with_context.py" "pids/enterprise_backend_contextual.pid"

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 5

echo ""
echo "🔍 Checking service status..."

# Check Brain Router
if [ -f "pids/brain_router_contextual.pid" ]; then
    brain_pid=$(cat "pids/brain_router_contextual.pid")
    if kill -0 "$brain_pid" 2>/dev/null; then
        echo "   ✅ Enhanced Brain Router (PID: $brain_pid) - ws://localhost:8765"
    else
        echo "   ❌ Enhanced Brain Router failed to start"
    fi
else
    echo "   ❌ Enhanced Brain Router PID file not found"
fi

# Check Enterprise Backend
if [ -f "pids/enterprise_backend_contextual.pid" ]; then
    backend_pid=$(cat "pids/enterprise_backend_contextual.pid")
    if kill -0 "$backend_pid" 2>/dev/null; then
        echo "   ✅ Enhanced Enterprise Backend (PID: $backend_pid) - ws://localhost:8767"
    else
        echo "   ❌ Enhanced Enterprise Backend failed to start"
    fi
else
    echo "   ❌ Enhanced Enterprise Backend PID file not found"
fi

echo ""
echo "📊 System Features Active:"
echo "   🔍 Semantic Memory Search"
echo "   🧠 Contextual Response Generation"
echo "   📚 Persistent Learning"
echo "   🎯 Mode-Specific Context Integration"
echo "   💯 Confidence Scoring"
echo "   🔄 Real-time Memory Updates"

echo ""
echo "🎯 Available Modes (All Contextual):"
echo "   🎯 Agent Mode - UI automation with context awareness"
echo "   💭 Ask Mode - Knowledge queries with memory search"
echo "   💡 Suggest Mode - Personalized recommendations"
echo "   🤖 General Mode - Contextual conversations"

echo ""
echo "🌐 WebSocket Endpoints:"
echo "   Brain Router: ws://localhost:8765"
echo "   Enterprise Backend: ws://localhost:8767"

echo ""
echo "📁 Log Files:"
echo "   Brain Router: logs/enhanced_brain_router.log"
echo "   Enterprise Backend: logs/backend/enhanced_enterprise_8767_context.log"

echo ""
echo "✅ Enhanced Contextual AI System started successfully!"
echo "🧠 All responses now include semantic memory context"
echo "📊 System learns and improves from every interaction"

echo ""
echo "To stop the system, run: ./STOP_CONTEXTUAL_SYSTEM.sh"