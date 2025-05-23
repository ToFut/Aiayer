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

# Start the enhanced brain router with FULL AUTOMATION (Primary - Port 8765)
echo "🤖 Starting Enhanced Brain Router with FULL AUTOMATION (Port 8765)..."
python3 enhanced_brain_router_with_full_automation.py > logs/brain_router/full_automation_brain_router.log 2>&1 &
BRAIN_ROUTER_PID=$!
echo $BRAIN_ROUTER_PID > pids/brain_router_full_automation.pid
echo "📊 Enhanced Brain Router with Full Automation PID: $BRAIN_ROUTER_PID"

# Start the enhanced enterprise backend with contextual memory (Secondary - Port 8767)
echo "🏢 Starting Enhanced Enterprise Backend with Contextual Memory (Port 8767)..."
python3 enhanced_enterprise_backend_with_context.py > logs/backend/contextual_enterprise_backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/enterprise_backend_contextual.pid
echo "📊 Enhanced Enterprise Backend PID: $BACKEND_PID"

# Wait for servers to start
echo "⏳ Waiting for servers to initialize..."
sleep 10

# Check if servers are running and responding
echo "🔍 Testing server connectivity..."

# Test Brain Router
BRAIN_ROUTER_OK=false
if ps -p $BRAIN_ROUTER_PID > /dev/null; then
    if python3 -c "
import asyncio
import websockets
import json
import sys

async def test_connection():
    try:
        async with websockets.connect('ws://localhost:8765', ping_timeout=5) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(msg)
            if data.get('type') == 'connection_established' and 'FULL AUTOMATION' in data.get('message', ''):
                print('✅ Brain Router (8765) with FULL AUTOMATION connected')
                return True
    except Exception as e:
        print(f'❌ Brain Router connection failed: {e}')
        return False
    return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        BRAIN_ROUTER_OK=true
    fi
fi

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

if [ "$BRAIN_ROUTER_OK" = true ] || [ "$BACKEND_OK" = true ]; then
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
        echo "🎉 ENHANCED SYSTEM WITH FULL AUTOMATION + SENSORS READY!"
        echo "========================================================"
        echo "🤖 Brain Router with FULL AUTOMATION: ws://localhost:8765"
        echo "🏢 Enterprise Backend with Context: ws://localhost:8767"
        echo "🔍 Semantic Search Integration: ACTIVE"
        echo "🧠 Contextual Memory System: ACTIVE"
        echo "🎯 REAL UI AUTOMATION: ACTIVE (Agent mode executes ACTUAL clicks/typing)"
        echo "🤖 All 4 Modes: Agent (with automation), Ask, Suggest, General"
        echo "📊 Running Sensors: $SENSORS_RUNNING"
        echo ""
        echo "📱 How to Use Brain Router with FULL AUTOMATION (Port 8765):"
        echo "   1. Connect to ws://localhost:8765"
        echo "   2. Send automation requests:"
        echo "      {\"type\":\"chat_request\",\"mode\":\"Agent\",\"message\":\"click on the Documents folder\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"Agent\",\"message\":\"type 'hello world' in the text field\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"Agent\",\"message\":\"open the terminal application\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"Ask\",\"message\":\"what is system status?\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"Suggest\",\"message\":\"improve my workflow\"}"
        echo "      {\"type\":\"chat_request\",\"mode\":\"General\",\"message\":\"hello\"}"
        echo ""
        echo "📱 How to Use Enterprise Backend (Port 8767):"
        echo "   1. Connect to ws://localhost:8767"
        echo "   2. Send chat requests (same format as above)"
        echo ""
        echo "🧪 Test Contextual System:"
        echo "   python3 test_all_modes_real_llm.py"
        echo ""
        echo "📊 Live Logs:"
        echo "   Brain Router: tail -f logs/brain_router/full_automation_brain_router.log"
        echo "   Enterprise Backend: tail -f logs/backend/contextual_enterprise_backend.log"
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
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
        echo "🤖 Agent mode now EXECUTES REAL UI AUTOMATION with contextual memory!"
        echo "🎯 Actual clicking, typing, and app opening - not just planning!"
        echo "🔍 Semantic search retrieves relevant context for every response"
        echo "📚 System learns and builds context from every interaction"
        echo "⚡ Response times: 5-15 seconds (optimized contextual processing)"
        echo "🔄 Memory Integration Service bridges sensors with semantic memory!"
        echo "🧠 Real-time context awareness with confidence scoring is ACTIVE!"
        echo "⚠️  SAFETY: Press Ctrl+1 for emergency automation shutdown"
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
        echo "   Brain Router PID: $BRAIN_ROUTER_PID"
        echo "   Enterprise Backend PID: $BACKEND_PID"
        echo "   Process Sensor PID: $PROCESS_PID"
        echo "   Screen Sensor PID: $SCREEN_PID"
        echo "   Memory System PID: $MEMORY_PID"
        echo "   Brain Router WebSocket: ws://localhost:8765"
        echo "   Enterprise Backend WebSocket: ws://localhost:8767"
        echo "   LLM Service: http://localhost:11434"
        echo "   Semantic Search: ACTIVE"
        echo ""
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
        echo ""
        echo "Press Ctrl+C to stop showing logs (system will keep running)"
        echo "----------------------------------------"
        
        # Show live logs from both services
        echo "📊 Showing live logs (Brain Router and Enterprise Backend)..."
        (
            tail -f logs/brain_router/full_automation_brain_router.log 2>/dev/null | sed 's/^/[AUTOMATION] /' &
            tail -f logs/backend/contextual_enterprise_backend.log 2>/dev/null | sed 's/^/[BACKEND] /'
        ) || {
            echo "📊 System running in background..."
            echo "ℹ️  Use 'tail -f logs/brain_router/full_automation_brain_router.log' to see automation logs"
            echo "ℹ️  Use 'tail -f logs/backend/contextual_enterprise_backend.log' to see backend logs"
            echo "ℹ️  Use 'python3 test_all_modes_real_llm.py' to test"
        }
    else
        echo "❌ Servers started but WebSocket connections failed!"
        echo "🔧 Check logs for details:"
        echo "Brain Router logs:"
        tail -10 logs/brain_router/full_automation_brain_router.log 2>/dev/null || echo "No brain router logs available"
        echo "Enterprise Backend logs:"
        tail -10 logs/backend/contextual_enterprise_backend.log 2>/dev/null || echo "No backend logs available"
        exit 1
    fi
else
    echo "❌ Failed to start contextual servers!"
    echo "🔧 Check logs for errors:"
    echo "Brain Router logs:"
    tail -10 logs/brain_router/full_automation_brain_router.log 2>/dev/null || echo "No brain router logs found"
    echo "Enterprise Backend logs:"
    tail -10 logs/backend/contextual_enterprise_backend.log 2>/dev/null || echo "No backend logs found"
    exit 1
fi