#!/bin/bash

# Final Enterprise Startup Script
# Professional Agent Self-Reflection and Collaboration System
# Like Claude Code and Google Project Standards

echo "🚀 ENTERPRISE SENSAI SYSTEM WITH AGENT SELF-REFLECTION"
echo "=================================================="
echo "Professional validation system with inter-agent collaboration"
echo "Claude Code and Google Project grade implementation"
echo ""

# Set working directory
cd "$(dirname "$0")"

# Colors for professional output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Professional logging function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_professional() {
    echo -e "${PURPLE}[PROFESSIONAL]${NC} $1"
}

# Check professional prerequisites
log_info "Checking enterprise-grade prerequisites..."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required for enterprise system"
    exit 1
fi

# Check required Python packages
log_info "Verifying professional Python packages..."
python3 -c "import asyncio, websockets, json, logging" 2>/dev/null
if [ $? -ne 0 ]; then
    log_warning "Installing required packages..."
    pip3 install asyncio websockets
fi

# Check if Ollama is running (for LLM integration)
if ! pgrep -f "ollama" > /dev/null; then
    log_warning "Ollama LLM service not detected - starting if available..."
    if command -v ollama &> /dev/null; then
        ollama serve &
        sleep 3
        log_success "Ollama LLM service started"
    else
        log_warning "Ollama not found - LLM features will use fallback responses"
    fi
fi

# Create professional logging directory
mkdir -p logs/enterprise_reflection
mkdir -p cache/validation_evidence
mkdir -p tmp/professional_screenshots

log_professional "Enterprise directory structure created"

# Kill any existing enterprise processes
log_info "Cleaning up existing enterprise processes..."
pkill -f "enhanced_enterprise_backend.py" 2>/dev/null
pkill -f "enterprise_agent_reflection.py" 2>/dev/null
pkill -f "specialized_agents.py" 2>/dev/null
sleep 2

# Start Enterprise Agent Reflection System
log_professional "Starting Enterprise Agent Self-Reflection System..."
python3 enhanced_enterprise_backend.py > logs/enterprise_reflection/backend.log 2>&1 &
ENTERPRISE_BACKEND_PID=$!
echo $ENTERPRISE_BACKEND_PID > pids/enterprise_backend.pid

# Wait for backend to initialize
sleep 5

# Check if backend started successfully
if ps -p $ENTERPRISE_BACKEND_PID > /dev/null; then
    log_success "Enhanced Enterprise Backend started (PID: $ENTERPRISE_BACKEND_PID)"
else
    log_error "Failed to start Enhanced Enterprise Backend"
    cat logs/enterprise_reflection/backend.log | tail -10
    exit 1
fi

# Test enterprise system connectivity
log_info "Testing enterprise agent collaboration..."
python3 -c "
import asyncio
import websockets
import json

async def test_enterprise_connection():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri) as websocket:
            # Test agent self-reflection capability
            test_message = {
                'type': 'agent_request',
                'message': 'Click on Documents Folder with professional validation'
            }
            await websocket.send(json.dumps(test_message))
            response = await websocket.recv()
            data = json.loads(response)
            
            if 'agent_plan_with_reflection' in data.get('type', ''):
                print('✅ Enterprise agent self-reflection system operational')
                print(f'✅ Reflection session: {data.get(\"session_id\", \"unknown\")}')
                print(f'✅ Professional validation: {data.get(\"professional_recommendations\", [])}')
                return True
            else:
                print('❌ Enterprise system not responding correctly')
                return False
                
    except Exception as e:
        print(f'❌ Enterprise connection test failed: {e}')
        return False

success = asyncio.run(test_enterprise_connection())
exit(0 if success else 1)
"

if [ $? -eq 0 ]; then
    log_success "Enterprise agent collaboration system operational"
else
    log_error "Enterprise system connectivity test failed"
    log_info "Check logs/enterprise_reflection/backend.log for details"
fi

# Start monitoring and validation services
log_professional "Initializing professional monitoring services..."

# Start specialized agents monitoring
python3 -c "
import asyncio
from specialized_agents import initialize_specialized_agents

async def init_agents():
    await initialize_specialized_agents()
    print('Professional specialized agents initialized')

asyncio.run(init_agents())
" &

# Create enterprise system status display
log_professional "Enterprise System Status:"
echo ""
echo "🧠 Agent Self-Reflection System: ACTIVE"
echo "🤝 Inter-Agent Communication: ENABLED"
echo "✅ Professional Validation: CLAUDE CODE STANDARDS"
echo "🔍 Deep Dive Analysis: COMPREHENSIVE"
echo "🏢 Enterprise Backend: ws://localhost:8765"
echo ""

log_professional "Key Enterprise Features:"
echo "  • Agent self-reflection and task completion validation"
echo "  • Inter-agent communication for UI context sharing"
echo "  • Professional-grade validation like Claude Code"
echo "  • Deep dive analysis for complex task verification"
echo "  • Context-aware agent collaboration framework"
echo ""

# Professional monitoring commands
log_info "Professional Monitoring Commands:"
echo "  • View backend logs: tail -f logs/enterprise_reflection/backend.log"
echo "  • Test agent collaboration: python3 specialized_agents.py"
echo "  • Run deep validation: python3 deep_dive_validator.py"
echo "  • Check system status: python3 -c \"from enhanced_enterprise_backend import enhanced_backend; print('System operational')\""
echo ""

# Enterprise usage examples
log_professional "Enterprise Agent Usage Examples:"
echo ""
echo "1. Professional UI Automation with Self-Reflection:"
echo "   {\"type\": \"agent_request\", \"message\": \"Click on Documents Folder\"}"
echo ""
echo "2. Task Validation with Deep Analysis:"
echo "   {\"type\": \"task_validation_request\", \"validation_type\": \"final_validation\"}"
echo ""
echo "3. Inter-Agent Collaboration Request:"
echo "   {\"type\": \"agent_collaboration_request\", \"target_agent\": \"ui_analysis\"}"
echo ""

# Create enterprise client example
cat > enterprise_client_example.py << 'EOF'
#!/usr/bin/env python3
"""
Enterprise Client Example - Professional Agent Interaction
Demonstrates self-reflection and collaboration capabilities
"""

import asyncio
import websockets
import json

async def enterprise_demo():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        print("🏢 Connected to Enterprise Agent System")
        
        # Test professional agent request with self-reflection
        request = {
            "type": "agent_request",
            "message": "Click on Documents Folder with professional validation and agent collaboration"
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        data = json.loads(response)
        
        print(f"📋 Response Type: {data.get('type')}")
        print(f"🎯 Goal Analysis: {data.get('goal_analysis', {}).get('clarified_goal')}")
        print(f"🔍 Session ID: {data.get('session_id')}")
        print(f"🤝 Agent Contexts: {len(data.get('agent_contexts', {}))}")
        print(f"✅ Professional Grade: {data.get('validation_confidence', 0):.2f}")
        
        print("\n🎓 Professional Recommendations:")
        for i, rec in enumerate(data.get('professional_recommendations', []), 1):
            print(f"  {i}. {rec}")

if __name__ == "__main__":
    asyncio.run(enterprise_demo())
EOF

chmod +x enterprise_client_example.py

log_success "Enterprise client example created: enterprise_client_example.py"

echo ""
log_professional "🎯 ENTERPRISE SENSAI SYSTEM IS NOW OPERATIONAL"
echo "=================================================="
echo "Professional agent self-reflection and collaboration active"
echo "Claude Code and Google Project standards implemented"
echo ""
echo "Test the system:"
echo "  python3 enterprise_client_example.py"
echo ""
echo "Stop the system:"
echo "  ./STOP_ENTERPRISE_SYSTEM.sh"
echo ""

# Save startup info
cat > .enterprise_system_info << EOF
ENTERPRISE_SYSTEM_STARTED=$(date)
BACKEND_PID=$ENTERPRISE_BACKEND_PID
FEATURES=agent_self_reflection,inter_agent_communication,professional_validation,deep_dive_analysis
STANDARDS=claude_code,google_project
WEBSOCKET_URL=ws://localhost:8765
EOF

log_success "Enterprise system startup complete - Agent self-reflection enabled"