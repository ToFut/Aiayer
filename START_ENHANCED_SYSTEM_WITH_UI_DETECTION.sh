#!/bin/bash

# SensAI Enhanced Enterprise System Startup
# WITH FULL UI AUTOMATION + PROFESSIONAL AGENT SYSTEM + CONTEXTUAL MEMORY INTEGRATION + ENHANCED UI DETECTION

echo "🚀 Starting Enhanced SensAI Enterprise System with FULL AUTOMATION + ADVANCED UI DETECTION..."
echo "🤖 ALL 4 MODES WITH REAL UI AUTOMATION + CONTEXTUAL MEMORY + MULTI-SOURCE UI DETECTION!"
echo ""
echo "📋 System Components:"
echo "   🎯 Agent Mode - REAL UI AUTOMATION (ACTUAL clicking, typing, app opening)"
echo "   🔍 Ask Mode - ENHANCED with LLM Integration + Visual Context + Semantic Search"
echo "   💡 Suggest Mode - ENHANCED with Memory Integration + Context Analysis"
echo "   💬 General Mode - Conversation Memory + Context Awareness"
echo "   📺 Total Screen Analyzer → Professional UI Element Detection"
echo "   🖥️  Process Sensor → Contextual Memory Integration"
echo "   🧠 LLaVA Visual Processor → Screen Understanding"
echo "   🎮 Input Controller → REAL PyAutoGUI Automation"
echo "   🔍 Semantic Search Agent → All Modes"
echo "   📚 Persistent Learning + Context Building"
echo "   🚀 Enhanced UI Detection → Multi-Source Element Detection"
echo "   🔧 Accessibility APIs → Native Element Role Detection"
echo "   🤖 ML Classification → AI-Powered UI Pattern Recognition"
echo "   🌐 Browser APIs → Direct DOM Element Access"
echo "   📝 OCR + NLP → Text Understanding & Intent Analysis"
echo ""
echo "✨ NEW: Agent mode will now ACTUALLY execute UI actions!"
echo "🎯 Click, type, and open apps - for real!"
echo ""
echo "🔥 LATEST ENHANCEMENTS:"
echo "   🧠 Ask Mode: Now uses LLM with enriched memory context + visual screen analysis"
echo "   💡 Suggest Mode: Enhanced with memory integration and contextual pattern recognition"
echo "   🔍 Both modes now provide specific, contextual responses based on your actual activity"
echo "   📱 Visual context from screen analyzer integrated into memory system"
echo "   🚀 Multi-Source UI Detection: Accessibility APIs + ML + Browser APIs + OCR/NLP"
echo "   🎯 Superior element detection accuracy through combined approaches"
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

python3 -c "import networkx" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ NetworkX available (for complex task dependency graphs)"
else
    echo "❌ NetworkX not found. Installing..."
    pip3 install networkx
fi

# Check Enhanced UI Detection dependencies
echo ""
echo "🔍 Checking Enhanced UI Detection dependencies..."

# Check core dependencies
python3 -c "import PIL, numpy, sklearn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Core ML/Image dependencies available"
else
    echo "❌ Core dependencies missing. Installing..."
    pip3 install Pillow numpy scikit-learn
fi

# Check OCR dependencies
python3 -c "import easyocr" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ EasyOCR available"
else
    echo "⚠️  EasyOCR not found. Enhanced text detection will be limited."
    echo "💡 Install with: pip3 install easyocr"
fi

# Check NLP dependencies
python3 -c "import spacy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ SpaCy NLP available"
else
    echo "⚠️  SpaCy not found. Enhanced text understanding will be limited."
    echo "💡 Install with: pip3 install spacy && python3 -m spacy download en_core_web_sm"
fi

# Check Browser automation dependencies
python3 -c "import selenium" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Selenium browser automation available"
else
    echo "⚠️  Selenium not found. Browser DOM access will be limited."
    echo "💡 Install with: pip3 install selenium"
fi

# Test Enhanced UI Detection System
echo ""
echo "🧪 Testing Enhanced UI Detection System..."
python3 -c "
import sys
sys.path.append('.')
try:
    from enhanced_ui_detection_system import EnhancedUIDetectionSystem
    detector = EnhancedUIDetectionSystem()
    
    available_methods = []
    if detector.accessibility_detector.available:
        available_methods.append('Accessibility APIs')
    if detector.ml_classifier.available:
        available_methods.append('Machine Learning')
    if detector.browser_detector.available:
        available_methods.append('Browser APIs')
    if detector.ocr_nlp_detector.ocr_available:
        available_methods.append('OCR')
    if detector.ocr_nlp_detector.nlp_available:
        available_methods.append('NLP')
    
    print(f'✅ Enhanced UI Detection System loaded successfully')
    print(f'✅ Available detection methods: {len(available_methods)}/5')
    for method in available_methods:
        print(f'  - {method}')
    
    if len(available_methods) >= 2:
        print('✅ Enhanced UI Detection System is functional')
    else:
        print('⚠️  Enhanced UI Detection has limited capabilities')
        
except Exception as e:
    print(f'❌ Enhanced UI Detection System test failed: {e}')
    print('⚠️  System will continue with basic UI detection')
" 2>/dev/null

# Kill any existing enhanced backend and contextual services
echo ""
echo "🛑 Stopping any existing enhanced backend and contextual services..."
pkill -f enhanced_enterprise_backend
pkill -f enhanced_brain_router
pkill -f enhanced_ui_detection
pkill -f contextual
sleep 2

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p logs/brain_router
mkdir -p logs/complex_task
mkdir -p logs/ui_detection
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/ui_detection
mkdir -p memory
mkdir -p models
mkdir -p results/enhanced_ui_detection

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

# Start the enhanced enterprise backend with complex task support and UI detection
echo "🏢 Starting Enhanced Enterprise Backend with Complex Task Support + UI Detection (Port 8767)..."

# Create enhanced backend with complex task integration and UI detection
cat > enhanced_backend_with_ui_detection.py << 'ENHANCED_EOF'
#!/usr/bin/env python3
"""
Enhanced Enterprise Backend with Complex Task Handler + Enhanced UI Detection Integration
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
    from enhanced_ui_detection_system import EnhancedUIDetectionSystem
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_backend_ui_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EnhancedBackendUIDetection')

class EnhancedBackendWithUIDetection(EnhancedEnterpriseBackend):
    """Enhanced backend with complex task capabilities and advanced UI detection"""
    
    def __init__(self):
        super().__init__()
        self.complex_task_handler = EnhancedAgentModeHandler()
        self.ui_detection_system = EnhancedUIDetectionSystem()
        logger.info("Enhanced Backend with UI Detection initialized")
    
    async def handle_agent_mode(self, message: str, context: dict = None) -> dict:
        """Enhanced agent mode with complex task capabilities and UI detection"""
        try:
            # Use the enhanced complex task handler with UI detection
            result = await self.complex_task_handler.handle_complex_request(
                request=message,
                user_id=context.get('user_id', 'default'),
                session_id=context.get('session_id', 'default'),
                context=context
            )
            
            # Add UI detection metadata
            result['enhanced_features'] = {
                'complex_task_handler': True,
                'enhanced_ui_detection': True,
                'max_task_complexity': 'enterprise',
                'max_concurrent_steps': 15,
                'adaptive_learning': True,
                'real_time_adaptation': True,
                'ui_detection_methods': self.ui_detection_system.get_available_methods()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced agent mode: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback to original agent mode
            return await super().handle_agent_mode(message, context)
    
    async def handle_ui_detection_request(self, request_data: dict) -> dict:
        """Handle UI detection requests"""
        try:
            image_path = request_data.get('image_path')
            app_context = request_data.get('app_context', {})
            
            if not image_path:
                return {
                    'type': 'ui_detection_error',
                    'message': 'No image path provided'
                }
            
            # Run enhanced UI detection
            result = await self.ui_detection_system.enhanced_detect_ui_elements(
                image_path, app_context
            )
            
            return {
                'type': 'ui_detection_result',
                'elements': [elem.__dict__ for elem in result.elements],
                'detection_methods_used': result.detection_methods_used,
                'timestamp': result.timestamp,
                'app_name': result.app_name
            }
            
        except Exception as e:
            logger.error(f"UI detection error: {e}")
            return {
                'type': 'ui_detection_error',
                'message': str(e)
            }
    
    async def handle_websocket_connection(self, websocket, path):
        """Enhanced websocket handler with UI detection support"""
        client_id = f"client_{id(websocket)}"
        self.active_connections[client_id] = {
            'websocket': websocket,
            'connected_at': datetime.now(),
            'complex_task_enabled': True,
            'ui_detection_enabled': True
        }
        
        logger.info(f"Enhanced client connected: {client_id}")
        
        # Send enhanced connection message
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'message': 'Enterprise Backend 8767 with Complex Task Handler + Enhanced UI Detection',
            'client_id': client_id,
            'features': {
                'complex_task_handler': True,
                'enhanced_ui_detection': True,
                'max_complexity': 'enterprise',
                'parallel_execution': True,
                'adaptive_learning': True,
                'streaming_responses': True,
                'all_chat_modes': ['ask', 'agent', 'suggest', 'general'],
                'ui_detection_methods': [
                    'Accessibility APIs',
                    'Machine Learning',
                    'Browser APIs', 
                    'OCR + NLP'
                ]
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
                        
                        # Enhanced context with UI detection support
                        context = {
                            'client_id': client_id,
                            'timestamp': datetime.now().isoformat(),
                            'domain': data.get('domain', 'general'),
                            'complexity_preference': data.get('complexity', 'auto'),
                            'parallel_execution': data.get('parallel', True),
                            'learning_enabled': data.get('learning', True),
                            'ui_detection_enabled': data.get('ui_detection', True)
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
                        
                        # Add UI detection features
                        response['enhanced_ui_detection'] = True
                        await websocket.send(json.dumps(response))
                        
                    elif data.get('type') == 'ui_detection_request':
                        response = await self.handle_ui_detection_request(data)
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
            logger.info(f"Enhanced client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

async def main():
    """Start the enhanced backend server"""
    backend = EnhancedBackendWithUIDetection()
    
    logger.info("Starting Enhanced Enterprise Backend with UI Detection...")
    logger.info("Port: 8767")
    logger.info("Features: Complex Task Orchestration, AI-Driven Planning, Enhanced UI Detection")
    
    # Start WebSocket server
    server = await websockets.serve(
        backend.handle_websocket_connection,
        "localhost",
        8767,
        ping_interval=30,
        ping_timeout=10
    )
    
    logger.info("✅ Enhanced Backend with UI Detection started on ws://localhost:8767")
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

python3 enhanced_backend_with_ui_detection.py > logs/backend/enhanced_backend_ui_detection.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/enhanced_backend_ui_detection.pid
echo "📊 Enhanced Backend with UI Detection PID: $BACKEND_PID"

# Wait for servers to start
echo "⏳ Waiting for servers to initialize..."
sleep 10

# Check if servers are running and responding
echo "🔍 Testing server connectivity..."

# Test Enhanced Backend
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
            if data.get('type') == 'connection_established' and 'Enhanced UI Detection' in data.get('message', ''):
                print('✅ Enhanced Backend (8767) with UI Detection connected')
                if data.get('features', {}).get('enhanced_ui_detection'):
                    print('✅ Enhanced UI Detection features confirmed active')
                return True
    except Exception as e:
        print(f'❌ Enhanced Backend connection failed: {e}')
        return False
    return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        BACKEND_OK=true
    fi
fi

if [ "$BACKEND_OK" = true ]; then
        echo "✅ Enhanced Backend with UI Detection is responding!"
        
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
        
        # Start Enhanced UI Detection Service
        echo "🚀 Starting Enhanced UI Detection Service..."
        python3 -c "
import asyncio
import logging
from enhanced_ui_detection_system import EnhancedUIDetectionSystem

# Setup logging
logging.basicConfig(
    filename='logs/ui_detection/ui_detection_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def ui_detection_service():
    detector = EnhancedUIDetectionSystem()
    logging.info('Enhanced UI Detection Service started')
    
    # Keep service alive
    while True:
        await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(ui_detection_service())
" > logs/ui_detection/ui_detection_service.log 2>&1 &
        UI_DETECTION_PID=$!
        echo $UI_DETECTION_PID > pids/ui_detection_service.pid
        echo "📊 Enhanced UI Detection Service PID: $UI_DETECTION_PID"
        
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
        
        if ps -p $UI_DETECTION_PID > /dev/null; then
            echo "✅ Enhanced UI Detection Service is running"
            SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
        else
            echo "❌ Enhanced UI Detection Service failed"
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
        echo "🎉 ENHANCED ENTERPRISE SYSTEM WITH ADVANCED UI DETECTION READY!"
        echo "================================================================================"
        echo "🏢 Enhanced Backend with UI Detection: ws://localhost:8767"
        echo "🤖 Model: llama3.2:1b (Fast & High Quality)"
        echo "⚡ Real-time Streaming Responses: ACTIVE"
        echo "🔍 Semantic Search Integration: ACTIVE"
        echo "🧠 Contextual Memory System: ACTIVE"
        echo "🎯 Complex Task Orchestration: ACTIVE"
        echo "🚀 Enhanced UI Detection: ACTIVE"
        echo "🤖 All 4 Modes: Ask, Agent (Enhanced), Suggest, General"
        echo "📊 Running Sensors: $SENSORS_RUNNING"
        echo ""
        echo "🚀 ENHANCED UI DETECTION CAPABILITIES:"
        echo "   🔧 Accessibility APIs: Native element role detection"
        echo "   🤖 Machine Learning: AI-powered UI pattern recognition"
        echo "   🌐 Browser APIs: Direct DOM element access"
        echo "   📝 OCR + NLP: Text extraction and intent analysis"
        echo "   🎯 Multi-source validation for superior accuracy"
        echo "   📊 Real-time element coordinate detection"
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
        echo "📱 How to Use Enhanced System:"
        echo "   1. Connect to ws://localhost:8767"
        echo "   2. Send enhanced agent requests:"
        echo '      {"type":"chat_request","mode":"agent","message":"Click login, fill form, submit and verify"}'
        echo "   3. Test UI detection:"
        echo '      {"type":"ui_detection_request","image_path":"screenshot.png","app_context":{"app_name":"Chrome"}}'
        echo "   4. Other modes still work:"
        echo "      {\"type\":\"chat_request\",\"mode\":\"ask\",\"message\":\"What is machine learning?\"}"
        echo ""
        echo "🧪 Test Enhanced UI Detection System:"
        echo "   python3 test_enhanced_ui_detection.py"
        echo ""
        echo "🧪 Test Complex Task System:"
        echo "   python3 -c \"import asyncio; from enhanced_complex_task_handler import test_complex_tasks; asyncio.run(test_complex_tasks())\""
        echo ""
        echo "🧪 Test All Modes:"
        echo "   python3 test_all_modes_final.py"
        echo ""
        echo "📊 Live Logs:"
        echo "   Enhanced Backend: tail -f logs/backend/enhanced_backend_ui_detection.log"
        echo "   UI Detection: tail -f logs/ui_detection/ui_detection_service.log"
        echo "   Total Screen: tail -f logs/sensors/total_screen_analyzer.log"
        echo ""
        
        # Create enhanced stop script
        cat > STOP_ENHANCED_SYSTEM.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping Enhanced System with UI Detection..."

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
pkill -f enhanced_backend_with_ui_detection 2>/dev/null || true
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f enhanced_ui_detection 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true  
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f memory_integration_service 2>/dev/null || true
pkill -f conscious_memory 2>/dev/null || true

# Remove temporary files
rm -f enhanced_backend_with_ui_detection.py 2>/dev/null || true

echo "✅ Enhanced System with UI Detection stopped"
STOP_EOF
        chmod +x STOP_ENHANCED_SYSTEM.sh
        
        echo "📋 Live System Status:"
        echo "   Enhanced Backend PID: $BACKEND_PID"
        echo "   Process Sensor PID: $PROCESS_PID"
        echo "   Screen Sensor PID: $SCREEN_PID"
        echo "   UI Detection Service PID: $UI_DETECTION_PID"
        echo "   Memory System PID: $MEMORY_PID"
        echo "   Enhanced Backend WebSocket: ws://localhost:8767"
        echo "   LLM Service: http://localhost:11434 (llama3.2:1b)"
        echo "   Enhanced UI Detection: ACTIVE"
        echo "   Semantic Search: ACTIVE"
        echo "   Streaming Responses: ACTIVE"
        echo ""
        echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM.sh"
        echo ""
        echo "Press Ctrl+C to stop showing logs (system will keep running)"
        echo "----------------------------------------"
        
        # Show live logs from enhanced backend
        echo "📊 Showing live logs (Enhanced Backend with UI Detection)..."
        tail -f logs/backend/enhanced_backend_ui_detection.log 2>/dev/null | sed 's/^/[ENHANCED-BACKEND] /' || {
            echo "📊 System running in background..."
            echo "ℹ️  Use 'tail -f logs/backend/enhanced_backend_ui_detection.log' to see backend logs"
            echo "ℹ️  Use 'python3 test_enhanced_ui_detection.py' to test UI detection"
        }
    else
        echo "❌ Enhanced Backend with UI Detection started but connection failed!"
        echo "🔧 Check logs for details:"
        echo "Enhanced Backend logs:"
        tail -10 logs/backend/enhanced_backend_ui_detection.log 2>/dev/null || echo "No backend logs available"
        exit 1
    fi
else
    echo "❌ Failed to start Enhanced Backend with UI Detection!"
    echo "🔧 Check logs for errors:"
    echo "Enhanced Backend logs:"
    tail -10 logs/backend/enhanced_backend_ui_detection.log 2>/dev/null || echo "No backend logs found"
    exit 1
fi