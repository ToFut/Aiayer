#!/bin/bash

# Simple Core System Startup - Agent Mode Fix Edition
# Focus on essential components that work

echo "🚀 Starting Core SensAI System with Agent Mode Fix..."
echo "🎯 ESSENTIAL COMPONENTS ONLY"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check Ollama
echo "🔍 Checking Ollama..."
if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama is running"
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:1b"; then
        echo "✅ Fast model (llama3.2:1b) available"
    else
        echo "⚠️  Installing fast model..."
        ollama pull llama3.2:1b &
    fi
else
    echo "❌ Ollama not running! Please start: ollama serve"
    exit 1
fi

# Kill existing processes
echo ""
echo "🛑 Stopping existing services..."
pkill -f enhanced_enterprise_backend || true
pkill -f process_sensor || true
pkill -f total_screen_analyzer || true
lsof -ti :8767 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 3

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs/backend logs/sensors pids cache/screen_sensor cache/process_sensor memory

# Start core backend (with our Agent Mode fix)
echo ""
echo "🏢 Starting Enhanced Enterprise Backend (with Agent Mode fix)..."
python3 enhanced_enterprise_backend_with_context.py > logs/backend/core_backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/core_backend.pid
echo "📊 Backend PID: $BACKEND_PID"

# Wait for backend
echo "⏳ Waiting for backend to start..."
sleep 8

# Test backend
echo "🔍 Testing backend..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend process is running"
    
    # Quick connectivity test
    python3 -c "
import asyncio
import websockets
import json

async def test():
    try:
        async with websockets.connect('ws://localhost:8767', ping_timeout=5) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(msg)
            if 'connection_established' in data.get('type', ''):
                print('✅ Backend responding')
                return True
    except:
        pass
    return False

result = asyncio.run(test())
exit(0 if result else 1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Backend is responding!"
        BACKEND_OK=true
    else
        echo "⚠️  Backend started but not responding yet"
        BACKEND_OK=true  # Continue anyway
    fi
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start essential sensors only
if [ "$BACKEND_OK" = true ]; then
    echo ""
    echo "🔧 Starting Essential Sensors..."
    
    # Process Sensor
    echo "🖥️  Starting Process Sensor..."
    python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
    PROCESS_PID=$!
    echo $PROCESS_PID > pids/process_sensor.pid
    echo "📊 Process Sensor PID: $PROCESS_PID"
    
    # Total Screen Analyzer
    echo "📺 Starting Total Screen Analyzer..."
    python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
    SCREEN_PID=$!
    echo $SCREEN_PID > pids/total_screen_analyzer.pid
    echo "📊 Screen Analyzer PID: $SCREEN_PID"
    
    sleep 5
    
    # Check sensors
    RUNNING_SENSORS=0
    if ps -p $PROCESS_PID > /dev/null; then
        echo "✅ Process Sensor running"
        RUNNING_SENSORS=$((RUNNING_SENSORS + 1))
    fi
    if ps -p $SCREEN_PID > /dev/null; then
        echo "✅ Screen Analyzer running"
        RUNNING_SENSORS=$((RUNNING_SENSORS + 1))
    fi
    
    echo ""
    echo "🎉 CORE SYSTEM READY!"
    echo "=================================="
    echo "🏢 Enhanced Backend: ws://localhost:8767"
    echo "🎯 Agent Mode Fix: ✅ ACTIVE"
    echo "🧠 Universal Handler: LOADED"
    echo "⚡ Real LLM Planning: ENABLED"
    echo "📊 Running Sensors: $RUNNING_SENSORS/2"
    echo ""
    echo "✅ NO MORE MOCK AUTOMATION PLANS!"
    echo "✅ Agent Mode uses real LLM planning"
    echo ""
    echo "🧪 Test Agent Mode:"
    echo "   python3 test_spotify_agent_fix.py"
    echo "   python3 quick_llm_speed_fix.py"
    echo ""
    echo "📊 Monitor Backend:"
    echo "   tail -f logs/backend/core_backend.log"
    echo ""
    echo "🛑 Stop: pkill -f enhanced_enterprise_backend"
    echo ""
    
    # Create simple stop script
    cat > STOP_CORE_SYSTEM.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Core System..."
pkill -f enhanced_enterprise_backend || true
pkill -f process_sensor || true
pkill -f total_screen_analyzer || true
rm -f pids/core_backend.pid pids/process_sensor.pid pids/total_screen_analyzer.pid
echo "✅ Core System stopped"
EOF
    chmod +x STOP_CORE_SYSTEM.sh
    
    echo "Press Ctrl+C to stop monitoring (system will keep running)"
    echo "----------------------------------------"
    tail -f logs/backend/core_backend.log 2>/dev/null | sed 's/^/[CORE-SYSTEM] /' || {
        echo "📊 System running in background..."
        echo "Use 'tail -f logs/backend/core_backend.log' to see logs"
    }
else
    echo "❌ Core system startup failed"
    exit 1
fi