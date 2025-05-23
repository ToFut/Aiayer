#!/bin/bash

# Start SensAI System with Brain Router
# Latest modes with centralized intelligence hub

echo "🧠 STARTING SENSAI BRAIN ROUTER SYSTEM"
echo "======================================"
echo "🎯 Modes: Agent | Ask | Suggest | General"
echo "🔗 Brain Router: Central Intelligence Hub"
echo ""

# Stop any existing processes
echo "🛑 Cleaning up existing processes..."
pkill -f "enhanced_enterprise_backend.py" 2>/dev/null
pkill -f "brain_router.py" 2>/dev/null
pkill -f "total_screen_analyzer.py" 2>/dev/null
pkill -f "enhanced_fixed_process_sensor.py" 2>/dev/null
sleep 2

# Create required directories
mkdir -p logs/brain_router
mkdir -p logs/sensors
mkdir -p logs/backend
mkdir -p pids

echo "🚀 Starting Brain Router System Components..."

# Start Brain Router WebSocket Server
echo "📡 Starting Brain Router (Port 8765)..."
python3 brain/core/brain_router.py > logs/brain_router/brain_router.log 2>&1 &
BRAIN_PID=$!
echo $BRAIN_PID > pids/brain_router.pid
sleep 3

# Start Screen Analyzer
echo "👁️ Starting Total Screen Analyzer..."
python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
SCREEN_PID=$!
echo $SCREEN_PID > pids/total_screen_analyzer.pid
sleep 2

# Start Process Sensor
echo "⚙️ Starting Enhanced Process Sensor..."
python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
PROCESS_PID=$!
echo $PROCESS_PID > pids/process_sensor.pid
sleep 2

# Verify connections
echo ""
echo "🔍 Verifying system connectivity..."
sleep 2

# Test brain router connectivity
python3 -c "
import asyncio
import websockets
import json
import sys

async def test_brain_router():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri) as websocket:
            message = {
                'type': 'chat_request',
                'mode': 'Ask',
                'message': 'System status check'
            }
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            print('✅ Brain Router: CONNECTED')
            return True
    except Exception as e:
        print(f'❌ Brain Router: FAILED - {e}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_brain_router())
    sys.exit(0 if result else 1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SENSAI BRAIN ROUTER SYSTEM READY!"
    echo "=================================="
    echo "🌐 WebSocket: ws://localhost:8765"
    echo "🧠 Brain Router: ACTIVE"
    echo "📡 Available Modes:"
    echo "   • Agent Mode  - Task execution & UI automation" 
    echo "   • Ask Mode    - Memory queries & knowledge retrieval"
    echo "   • Suggest Mode - Proactive suggestions & optimization"
    echo "   • General Mode - Basic LLM conversations"
    echo ""
    echo "📋 Usage Example:"
    echo "{"
    echo '  "type": "chat_request",'
    echo '  "mode": "Agent",'
    echo '  "message": "Click on Documents folder"'
    echo "}"
    echo ""
    echo "📊 System Status:"
    echo "   Brain Router: ✅ $(cat pids/brain_router.pid)"
    echo "   Screen Sensor: ✅ $(cat pids/total_screen_analyzer.pid)" 
    echo "   Process Sensor: ✅ $(cat pids/process_sensor.pid)"
    echo ""
    echo "📝 Logs: logs/brain_router/, logs/sensors/"
    echo "🛑 Stop: ./stop_brain_router_system.sh"
else
    echo "❌ SYSTEM STARTUP FAILED"
    echo "Check logs for details."
    exit 1
fi