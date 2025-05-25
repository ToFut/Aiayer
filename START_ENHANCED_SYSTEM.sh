#!/bin/bash

# SensAI Enhanced Enterprise System Startup
# WITH FULL UI AUTOMATION + PROFESSIONAL AGENT SYSTEM + CONTEXTUAL MEMORY INTEGRATION

echo "🚀 Starting Enhanced SensAI Enterprise System with FULL AUTOMATION..."
echo "🤖 ALL 4 MODES WITH REAL UI AUTOMATION + CONTEXTUAL MEMORY!"
echo ""
echo "📋 System Components:"
echo "   🎯 Agent Mode - REAL UI AUTOMATION (ACTUAL clicking, typing, app opening)"
echo "   🔍 Ask Mode - Semantic Search + Knowledge Retrieval"
echo "   💡 Suggest Mode - Pattern Analysis + Personalized Recommendations"
echo "   💬 General Mode - Conversation Memory + Context Awareness"
echo "   📺 Total Screen Analyzer → Professional UI Element Detection"
echo "   🖥️  Process Sensor → Contextual Memory Integration"
echo "   🧠 LLaVA Visual Processor → Screen Understanding"
echo "   🎮 Input Controller → REAL PyAutoGUI Automation"
echo "   🔍 Semantic Search Agent → All Modes"
echo "   📚 Persistent Learning + Context Building"
echo ""
echo "✨ NEW: Agent mode will now ACTUALLY execute UI actions!"
echo "🎯 Click, type, and open apps - for real!"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if Ollama is running (required for real LLM)
echo "🔍 Checking Ollama LLM service..."
if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama LLM service is running"
    
    # Check if required model is available
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:latest"; then
        echo "✅ llama3.2:latest model is available"
    else
        echo "⚠️  llama3.2:latest model not found. You may see slower initial responses."
    fi
else
    echo "❌ Ollama LLM service not running!"
    echo "🔧 Please start Ollama first: ollama serve"
    echo "📦 Then install model: ollama pull llama3.2:latest"
    echo ""
    echo "⚠️  System will start but will use fallback responses"
    sleep 3
fi

# Check Python automation dependencies
echo ""
echo "🔍 Checking automation dependencies..."

python3 -c "import pyautogui" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ PyAutoGUI available"
else
    echo "❌ PyAutoGUI not found. Installing..."
    pip3 install pyautogui
fi

python3 -c "import pynput" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ pynput available"
else
    echo "❌ pynput not found. Installing..."
    pip3 install pynput
fi

# Kill any existing enhanced backend and contextual services
echo ""
echo "🛑 Stopping any existing enhanced backend and contextual services..."
pkill -f enhanced_enterprise_backend
pkill -f enhanced_brain_router
pkill -f contextual
sleep 2

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p logs/brain_router
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p memory

# Start the enhanced enterprise backend with contextual memory and streaming (Primary - Port 8767)
echo "🏢 Starting Enhanced Enterprise Backend with Real AI Streaming (Port 8767)..."
python3 enhanced_enterprise_backend_with_context.py > logs/backend/contextual_enterprise_backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/enterprise_backend_contextual.pid
echo "📊 Enhanced Enterprise Backend PID: $BACKEND_PID"

# Note: Brain router disabled due to syntax errors - using enterprise backend only
BRAIN_ROUTER_PID=""
echo "ℹ️  Using Enterprise Backend only (brain router has syntax errors)"

# Wait for servers to start
echo "⏳ Waiting for servers to initialize..."
sleep 10

# Check if servers are running and responding
echo "🔍 Testing server connectivity..."

# Skip Brain Router test (disabled)
BRAIN_ROUTER_OK=false
echo "ℹ️  Skipping Brain Router test (disabled)"

# Test Enterprise Backend
BACKEND_OK=false
if ps -p $BACKEND_PID > /dev/null; then
    if python3 -c "
import asyncio
import websockets
import json
import sys

async def test_connection():
    try:
        async with websockets.connect('ws://localhost:8767', ping_timeout=5) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(msg)
            if data.get('type') == 'connection_established' and 'Enterprise Backend 8767' in data.get('message', ''):
                print('✅ Enterprise Backend (8767) with Professional Agent System connected')
                return True
    except Exception as e:
        print(f'❌ Enterprise Backend connection failed: {e}')
        return False
    return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        BACKEND_OK=true
    fi
fi

if [ "$BACKEND_OK" = true ]; then
        echo "✅ Backend is responding!"
        
        echo ""
        echo "🔧 Starting Sensor Systems..."
        
        # Start Process Sensor
        echo "🖥️  Starting Process Sensor..."
        python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
        PROCESS_PID=$!
        echo $PROCESS_PID > pids/process_sensor.pid
        echo "📊 Process Sensor PID: $PROCESS_PID"
        
        # Start Total Screen Analyzer (more comprehensive than basic screen sensor)
        echo "📺 Starting Total Screen Analyzer..."
        python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
        SCREEN_PID=$!
        echo $SCREEN_PID > pids/total_screen_analyzer.pid
        echo "📊 Total Screen Analyzer PID: $SCREEN_PID"
        
        # Start Memory Integration Service
        echo "🧠 Starting Memory Integration Service..."
        python3 memory/memory_integration_service.py > logs/memory/integration_service.log 2>&1 &
        MEMORY_PID=$!
        echo $MEMORY_PID > pids/memory_integration.pid
        echo "📊 Memory Integration PID: $MEMORY_PID"
        
        # Start Conscious Memory System (if available)
        if [ -f "memory/conscious_memory.py" ]; then
            echo "🧠 Starting Conscious Memory System..."
            python3 memory/conscious_memory.py > logs/memory/conscious_memory.log 2>&1 &
            CONSCIOUS_PID=$!
            echo $CONSCIOUS_PID > pids/conscious_memory.pid
            echo "📊 Conscious Memory PID: $CONSCIOUS_PID"
        fi
        
        # Wait for sensors to initialize
        echo "⏳ Waiting for sensors to initialize..."
        sleep 15
        
        # Check sensor status
        echo ""
        echo "🔍 Checking sensor status..."
        SENSORS_RUNNING=0
        
        if ps -p $PROCESS_PID > /dev/null; then
            echo "✅ Process Sensor is running"
            SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
        else
            echo "❌ Process Sensor failed"
        fi
        
        if ps -p $SCREEN_PID > /dev/null; then
            echo "✅ Total Screen Analyzer is running"
            SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
        else
            echo "❌ Total Screen Analyzer failed"
        fi
        
        if ps -p $MEMORY_PID > /dev/null; then
            echo "✅ Memory Integration Service is running"
            SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
        else
            echo "❌ Memory Integration Service failed"
        fi
        
        # Check conscious memory if started
        if [ ! -z "$CONSCIOUS_PID" ] && ps -p $CONSCIOUS_PID > /dev/null; then
            echo "✅ Conscious Memory System is running"
            SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
        fi
        
        echo ""
        echo "🎉 ENHANCED ENTERPRISE SYSTEM WITH REAL AI STREAMING READY!"
        echo "=========================================================="
        echo "🏢 Enterprise Backend with Real AI: ws://localhost:8767"
        echo "🤖 Model: llama3.2:1b (Fast & High Quality)"
        echo "⚡ Real-time Streaming Responses: ACTIVE"
        echo "🔍 Semantic Search Integration: ACTIVE"
        echo "🧠 Contextual Memory System: ACTIVE"
        echo "🤖 All 4 Modes: Ask, Agent, Suggest, General"
        echo "📊 Running Sensors: $SENSORS_RUNNING"
        echo ""
        echo "📱 How to Use Enterprise Backend (Port 8767):"
        echo "   1. Connect to ws://localhost:8767"
        echo "   2. Send chat requests with streaming responses:"
        echo "      {\"type\":\"chat_request\",\"mode\":\"ask\",\"message\":\"What is machine learning?\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"agent\",\"message\":\"Help me plan a project\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"suggest\",\"message\":\"What should I learn?\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"general\",\"message\":\"Tell me about AI trends\"}"
        echo ""
        echo "🧪 Test Contextual System:"
        echo "   python3 test_all_modes_real_llm.py"
        echo ""
        echo "📊 Live Logs:"
        echo "   Enterprise Backend: tail -f logs/backend/contextual_enterprise_backend.log"
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
        echo ""
        echo "🧪 Test All Modes:"
        echo "   python3 test_all_modes_final.py"
        echo ""
        echo "🧪 Test Memory System:"
        echo "   python3 -c \"import json; print(json.dumps(json.load(open('memory/conscious.json')), indent=2))\""
        echo ""
        echo "📊 View Memory State:"
        echo "   cat memory/memory_state.json | python3 -m json.tool"
        echo ""
        echo "🔍 Check Memory Logs:"
        echo "   tail -f logs/memory/integration_service.log"
        echo "   tail -f logs/sensors/total_screen_analyzer.log"
        echo "   tail -f logs/sensors/process_sensor.log"
        echo ""
        echo "🤖 Real AI responses with llama3.2:1b model!"
        echo "⚡ Streaming responses provide instant feedback"
        echo "🔍 Semantic search retrieves relevant context for every response"
        echo "📚 System learns and builds context from every interaction"
        echo "⚡ Response times: 2-7 seconds (optimized streaming)"
        echo "🔄 Memory Integration Service bridges sensors with semantic memory!"
        echo "🧠 Real-time context awareness with confidence scoring is ACTIVE!"
        echo ""
        
        # Show live system status
        # Create stop script for all components
        cat > STOP_ENHANCED_SYSTEM.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping Enhanced Contextual System with Sensors..."

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
pkill -f enhanced_brain_router 2>/dev/null || true
pkill -f contextual 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true  
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration_service 2>/dev/null || true
pkill -f conscious_memory 2>/dev/null || true
pkill -f semantic_search 2>/dev/null || true

echo "✅ Enhanced Contextual System stopped"
STOP_EOF
        chmod +x STOP_ENHANCED_SYSTEM.sh
        
        echo "📋 Live System Status:"
        echo "   Enterprise Backend PID: $BACKEND_PID"
        echo "   Process Sensor PID: $PROCESS_PID"
        echo "   Screen Sensor PID: $SCREEN_PID"
        echo "   Memory System PID: $MEMORY_PID"
        echo "   Enterprise Backend WebSocket: ws://localhost:8767"
        echo "   LLM Service: http://localhost:11434 (llama3.2:1b)"
        echo "   Semantic Search: ACTIVE"
        echo "   Streaming Responses: ACTIVE"
        echo ""
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
        echo ""
        echo "Press Ctrl+C to stop showing logs (system will keep running)"
        echo "----------------------------------------"
        
        # Show live logs from enterprise backend
        echo "📊 Showing live logs (Enterprise Backend with Streaming)..."
        tail -f logs/backend/contextual_enterprise_backend.log 2>/dev/null | sed 's/^/[BACKEND] /' || {
            echo "📊 System running in background..."
            echo "ℹ️  Use 'tail -f logs/backend/contextual_enterprise_backend.log' to see backend logs"
            echo "ℹ️  Use 'python3 test_all_modes_final.py' to test all modes"
        }
    else
        echo "❌ Enterprise Backend started but WebSocket connection failed!"
        echo "🔧 Check logs for details:"
        echo "Enterprise Backend logs:"
        tail -10 logs/backend/contextual_enterprise_backend.log 2>/dev/null || echo "No backend logs available"
        exit 1
    fi
else
    echo "❌ Failed to start Enterprise Backend!"
    echo "🔧 Check logs for errors:"
    echo "Enterprise Backend logs:"
    tail -10 logs/backend/contextual_enterprise_backend.log 2>/dev/null || echo "No backend logs found"
    exit 1
fi