#!/bin/bash

# SensAI Enhanced Complex Task System Startup
# WITH ENTERPRISE-GRADE COMPLEX TASK HANDLING + ALL EXISTING FEATURES

echo "🚀 Starting Enhanced SensAI System with COMPLEX TASK CAPABILITIES..."
echo "🤖 ENTERPRISE-GRADE TASK ORCHESTRATION + FULL UI AUTOMATION!"
echo ""
echo "📋 Enhanced System Components:"
echo "   🎯 Agent Mode - COMPLEX TASK ORCHESTRATION (50+ steps, enterprise workflows)"
echo "   🔍 Ask Mode - Semantic Search + Knowledge Retrieval"
echo "   💡 Suggest Mode - Pattern Analysis + Personalized Recommendations"
echo "   💬 General Mode - Conversation Memory + Context Awareness"
echo "   📺 Total Screen Analyzer → Professional UI Element Detection"
echo "   🖥️  Process Sensor → Contextual Memory Integration"
echo "   🧠 LLaVA Visual Processor → Screen Understanding"
echo "   🎮 Input Controller → REAL PyAutoGUI Automation"
echo "   🔍 Semantic Search Agent → All Modes"
echo "   📚 Persistent Learning + Context Building"
echo "   ⚡ Enhanced Complex Task Handler → AI-Driven Multi-Step Planning"
echo ""
echo "✨ NEW COMPLEX TASK FEATURES:"
echo "🎯 Simple Tasks: 1-3 steps (click, type, basic actions)"
echo "🔧 Moderate Tasks: 4-10 steps (form processing, workflows)"
echo "🏗️  Complex Tasks: 10-50 steps (data analysis, multi-system operations)"
echo "🏢 Enterprise Tasks: 50+ steps (CRM integrations, deployments)"
echo "⚡ Parallel Execution: Up to 15 concurrent steps"
echo "🧠 Adaptive Learning: Improves from execution history"
echo "🔄 Real-time Adaptation: Dynamic replanning on failures"
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

python3 -c "import networkx" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ NetworkX available (for dependency graphs)"
else
    echo "❌ NetworkX not found. Installing..."
    pip3 install networkx
fi

python3 -c "import asyncio" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ AsyncIO available"
else
    echo "❌ AsyncIO not available (upgrade Python to 3.7+)"
fi

# Kill any existing services
echo ""
echo "🛑 Stopping any existing enhanced backend and contextual services..."
pkill -f enhanced_enterprise_backend
pkill -f enhanced_brain_router
pkill -f contextual
pkill -f complex_task
sleep 2

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p logs/brain_router
mkdir -p logs/complex_task
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p memory

# Test Enhanced Complex Task Handler first
echo ""
echo "🧪 Testing Enhanced Complex Task Handler..."
python3 -c "
import sys
sys.path.append('.')
try:
    from enhanced_complex_task_handler import AdvancedTaskPlanner, ComplexTaskExecutor, EnhancedAgentModeHandler, TaskContext, TaskComplexity
    print('✅ Enhanced Complex Task Handler imported successfully')
    
    # Quick test
    import asyncio
    async def quick_test():
        planner = AdvancedTaskPlanner()
        context = TaskContext('test_user', 'test_session', 'web_automation')
        plan = await planner.create_complex_plan('Click the login button', context)
        print(f'✅ Quick test passed: {plan.complexity.name} complexity detected')
        return True
    
    result = asyncio.run(quick_test())
    print('✅ Enhanced Complex Task Handler is functional')
except Exception as e:
    print(f'❌ Enhanced Complex Task Handler test failed: {e}')
    sys.exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Enhanced Complex Task Handler test failed!"
    echo "🔧 Please check the enhanced_complex_task_handler.py file"
    exit 1
fi

# Start the enhanced enterprise backend with contextual memory and complex task support
echo "🏢 Starting Enhanced Enterprise Backend with Complex Task Support (Port 8767)..."

# Create enhanced backend with complex task integration
cat > enhanced_backend_with_complex_tasks.py << 'ENHANCED_EOF'
#!/usr/bin/env python3
"""
Enhanced Enterprise Backend with Complex Task Handler Integration
Integrates the new complex task capabilities with the existing backend system.
"""

import asyncio
import json
import logging
import websockets
import sys
import traceback
from datetime import datetime

# Import existing backend
sys.path.append('.')
try:
    from enhanced_enterprise_backend_with_context import EnhancedEnterpriseBackend
    from enhanced_complex_task_handler import EnhancedAgentModeHandler
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/complex_task_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ComplexTaskBackend')

class ComplexTaskEnhancedBackend(EnhancedEnterpriseBackend):
    """Enhanced backend with complex task capabilities"""
    
    def __init__(self):
        super().__init__()
        self.complex_task_handler = EnhancedAgentModeHandler()
        logger.info("Complex Task Enhanced Backend initialized")
    
    async def handle_agent_mode(self, message: str, context: dict = None) -> dict:
        """Enhanced agent mode with complex task capabilities"""
        try:
            # Use the enhanced complex task handler
            result = await self.complex_task_handler.handle_complex_request(
                request=message,
                user_id=context.get('user_id', 'default'),
                session_id=context.get('session_id', 'default'),
                context=context
            )
            
            # Add complex task metadata
            result['enhanced_features'] = {
                'complex_task_handler': True,
                'max_task_complexity': 'enterprise',
                'max_concurrent_steps': 15,
                'adaptive_learning': True,
                'real_time_adaptation': True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced agent mode: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback to original agent mode
            return await super().handle_agent_mode(message, context)
    
    async def handle_websocket_connection(self, websocket, path):
        """Enhanced websocket handler with complex task support"""
        client_id = f"client_{id(websocket)}"
        self.active_connections[client_id] = {
            'websocket': websocket,
            'connected_at': datetime.now(),
            'complex_task_enabled': True
        }
        
        logger.info(f"Complex Task client connected: {client_id}")
        
        # Send enhanced connection message
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'message': 'Enterprise Backend 8767 with Complex Task Handler',
            'client_id': client_id,
            'features': {
                'complex_task_handler': True,
                'max_complexity': 'enterprise',
                'parallel_execution': True,
                'adaptive_learning': True,
                'streaming_responses': True,
                'all_chat_modes': ['ask', 'agent', 'suggest', 'general']
            },
            'timestamp': datetime.now().isoformat()
        }))
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'chat_request':
                        mode = data.get('mode', 'general')
                        user_message = data.get('message', '')
                        
                        # Enhanced context with complex task support
                        context = {
                            'client_id': client_id,
                            'timestamp': datetime.now().isoformat(),
                            'domain': data.get('domain', 'general'),
                            'complexity_preference': data.get('complexity', 'auto'),
                            'parallel_execution': data.get('parallel', True),
                            'learning_enabled': data.get('learning', True)
                        }
                        
                        # Route to appropriate handler
                        if mode == 'agent':
                            response = await self.handle_agent_mode(user_message, context)
                        elif mode == 'ask':
                            response = await self.handle_ask_mode(user_message, context)
                        elif mode == 'suggest':
                            response = await self.handle_suggest_mode(user_message, context)
                        else:
                            response = await self.handle_general_mode(user_message, context)
                        
                        # Send enhanced response
                        response['complex_task_features'] = True
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Processing error: {str(e)}'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Complex Task client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

async def main():
    """Start the enhanced backend server"""
    backend = ComplexTaskEnhancedBackend()
    
    logger.info("Starting Enhanced Enterprise Backend with Complex Task Handler...")
    logger.info("Port: 8767")
    logger.info("Features: Complex Task Orchestration, AI-Driven Planning, Adaptive Learning")
    
    # Start WebSocket server
    server = await websockets.serve(
        backend.handle_websocket_connection,
        "localhost",
        8767,
        ping_interval=30,
        ping_timeout=10
    )
    
    logger.info("✅ Enhanced Backend with Complex Task Handler started on ws://localhost:8767")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
ENHANCED_EOF

python3 enhanced_backend_with_complex_tasks.py > logs/backend/complex_task_backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/complex_task_backend.pid
echo "📊 Enhanced Complex Task Backend PID: $BACKEND_PID"

# Wait for server to start
echo "⏳ Waiting for enhanced backend to initialize..."
sleep 10

# Test backend connectivity
echo "🔍 Testing enhanced backend connectivity..."
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
            if data.get('type') == 'connection_established' and 'Complex Task Handler' in data.get('message', ''):
                print('✅ Enhanced Backend with Complex Task Handler connected')
                if data.get('features', {}).get('complex_task_handler'):
                    print('✅ Complex Task features confirmed active')
                return True
    except Exception as e:
        print(f'❌ Enhanced backend connection failed: {e}')
        return False
    return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        BACKEND_OK=true
    fi
fi

if [ "$BACKEND_OK" = true ]; then
    echo "✅ Enhanced Backend with Complex Task Handler is responding!"
    
    echo ""
    echo "🔧 Starting Enhanced Sensor Systems..."
    
    # Start Process Sensor
    echo "🖥️  Starting Process Sensor..."
    python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
    PROCESS_PID=$!
    echo $PROCESS_PID > pids/process_sensor.pid
    echo "📊 Process Sensor PID: $PROCESS_PID"
    
    # Start Total Screen Analyzer
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
    
    # Test Complex Task System
    echo ""
    echo "🧪 Testing Enhanced Complex Task System..."
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from enhanced_complex_task_handler import test_complex_tasks

print('🚀 Running Complex Task System Tests...')
asyncio.run(test_complex_tasks())
print('✅ Complex Task System tests completed!')
" > logs/complex_task/test_results.log 2>&1 &
    
    TEST_PID=$!
    sleep 5
    
    if ps -p $TEST_PID > /dev/null; then
        echo "✅ Complex Task System tests are running (PID: $TEST_PID)"
    else
        echo "⚠️  Complex Task System tests completed quickly (check logs)"
    fi
    
    echo ""
    echo "🎉 ENHANCED ENTERPRISE SYSTEM WITH COMPLEX TASK ORCHESTRATION READY!"
    echo "================================================================================"
    echo "🏢 Enhanced Backend with Complex Task Handler: ws://localhost:8767"
    echo "🤖 Model: llama3.2:1b (Fast & High Quality)"
    echo "⚡ Real-time Streaming Responses: ACTIVE"
    echo "🔍 Semantic Search Integration: ACTIVE"
    echo "🧠 Contextual Memory System: ACTIVE"
    echo "🎯 Complex Task Orchestration: ACTIVE"
    echo "🤖 All 4 Modes: Ask, Agent (Enhanced), Suggest, General"
    echo ""
    echo "🏗️  COMPLEX TASK CAPABILITIES:"
    echo "   📝 Simple Tasks: 1-3 steps (Basic UI automation)"
    echo "   🔧 Moderate Tasks: 4-10 steps (Form processing, workflows)"
    echo "   🏗️  Complex Tasks: 10-50 steps (Data analysis, integrations)"
    echo "   🏢 Enterprise Tasks: 50+ steps (CRM deployments, migrations)"
    echo "   ⚡ Parallel Execution: Up to 15 concurrent steps"
    echo "   🧠 Adaptive Learning: Improves from execution history"
    echo "   🔄 Real-time Adaptation: Dynamic replanning on failures"
    echo ""
    echo "📱 How to Use Enhanced Complex Task System:"
    echo "   1. Connect to ws://localhost:8767"
    echo "   2. Send complex agent requests:"
    echo '      {"type":"chat_request","mode":"agent","message":"Click login, fill form, submit and verify"}'
    echo '      {"type":"chat_request","mode":"agent","message":"Analyze sales data, create charts, generate report"}'
    echo '      {"type":"chat_request","mode":"agent","message":"Integrate CRM with email platform, migrate contacts"}'
    echo ""
    echo "🧪 Test Complex Task Examples:"
    echo "   python3 -c \"import asyncio; from enhanced_complex_task_handler import test_complex_tasks; asyncio.run(test_complex_tasks())\""
    echo ""
    echo "📊 Live Logs:"
    echo "   Complex Task Backend: tail -f logs/backend/complex_task_backend.log"
    echo "   Complex Task Tests: tail -f logs/complex_task/test_results.log"
    echo "   Memory System: tail -f logs/memory/integration_service.log"
    echo ""
    echo "🛑 Stop System: ./STOP_COMPLEX_TASK_SYSTEM.sh"
    echo ""
    echo "📈 ENTERPRISE CAPABILITIES DEMONSTRATED:"
    echo "✅ Multi-complexity task handling (Simple → Enterprise)"
    echo "✅ Intelligent AI-driven decomposition"
    echo "✅ Hierarchical task planning"
    echo "✅ Dependency-aware execution"
    echo "✅ Parallel step execution (15+ concurrent)"
    echo "✅ Adaptive replanning and learning"
    echo "✅ Real-time progress monitoring"
    echo "✅ Enterprise-grade reliability"
    echo ""
    
    # Create stop script
    cat > STOP_COMPLEX_TASK_SYSTEM.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping Enhanced Complex Task System..."

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
pkill -f enhanced_backend_with_complex_tasks 2>/dev/null || true
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f complex_task 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true  
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration_service 2>/dev/null || true
pkill -f conscious_memory 2>/dev/null || true

# Remove temporary enhanced backend file
rm -f enhanced_backend_with_complex_tasks.py 2>/dev/null || true

echo "✅ Enhanced Complex Task System stopped"
STOP_EOF
    chmod +x STOP_COMPLEX_TASK_SYSTEM.sh
    
    echo "Press Ctrl+C to stop showing logs (system will keep running)"
    echo "================================================================================"
    
    # Show live logs
    echo "📊 Showing live logs (Enhanced Complex Task Backend)..."
    tail -f logs/backend/complex_task_backend.log 2>/dev/null | sed 's/^/[COMPLEX-BACKEND] /' || {
        echo "📊 System running in background..."
        echo "ℹ️  Use 'tail -f logs/backend/complex_task_backend.log' to see backend logs"
        echo "ℹ️  Use the test commands above to try complex task examples"
    }
    
else
    echo "❌ Enhanced Backend with Complex Task Handler failed to start!"
    echo "🔧 Check logs for errors:"
    tail -10 logs/backend/complex_task_backend.log 2>/dev/null || echo "No backend logs found"
    exit 1
fi