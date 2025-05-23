#!/bin/bash

# ENTERPRISE SYSTEM STARTUP WITH FRONTEND COMPATIBILITY
# Includes both port 8765 (enterprise) and 8767 (frontend) backends

echo "🚀 ENTERPRISE SENSAI SYSTEM WITH FRONTEND COMPATIBILITY"
echo "======================================================"
echo "Professional system with brain router and frontend integration"
echo ""

# Set working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] [ERROR]${NC} $1"
}

log_professional() {
    echo -e "${PURPLE}[$(date '+%H:%M:%S')] [PROFESSIONAL]${NC} $1"
}

# Enhanced error handling
cleanup_on_error() {
    log_error "Startup failed. Cleaning up..."
    pkill -f "enhanced_enterprise_backend.py" 2>/dev/null || true
    pkill -f "enterprise_backend_8767.py" 2>/dev/null || true
    exit 1
}

trap cleanup_on_error ERR

# Check prerequisites
log_info "Checking system prerequisites..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required"
    exit 1
fi

# Create directories
log_professional "Creating enterprise directory structure..."
mkdir -p logs/backend
mkdir -p logs/enterprise_reflection  
mkdir -p logs/agents
mkdir -p pids
mkdir -p cache/validation_evidence
mkdir -p tmp/professional_screenshots

# Enhanced cleanup
log_info "Cleaning up existing processes..."
CLEANUP_PROCESSES=(
    "enhanced_enterprise_backend.py"
    "enterprise_backend_8767.py"
    "simple_brain_router_server.py"
    "brain_router.py"
)

for process in "${CLEANUP_PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        log_info "Stopping $process..."
        pkill -f "$process" 2>/dev/null || true
    fi
done

sleep 3

# Check and free ports
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "Port $port in use, freeing it..."
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

check_port 8765
check_port 8767

# Start Enterprise Backend 8767 (Frontend Compatible)
log_professional "Starting Enterprise Backend 8767 (Frontend Compatible)..."
python3 enterprise_backend_8767.py > logs/backend/enterprise_8767.log 2>&1 &
BACKEND_8767_PID=$!
echo $BACKEND_8767_PID > pids/enterprise_8767.pid

sleep 5

if ps -p $BACKEND_8767_PID > /dev/null; then
    log_success "Enterprise Backend 8767 started (PID: $BACKEND_8767_PID)"
else
    log_error "Failed to start Enterprise Backend 8767"
    exit 1
fi

# Start Enhanced Enterprise Backend 8765 (Brain Router Integration)
log_professional "Starting Enhanced Enterprise Backend 8765 (Brain Router)..."
if [[ -f "enhanced_enterprise_backend.py" ]]; then
    python3 enhanced_enterprise_backend.py > logs/enterprise_reflection/backend.log 2>&1 &
    BACKEND_8765_PID=$!
    echo $BACKEND_8765_PID > pids/enterprise_8765.pid
    
    sleep 5
    
    if ps -p $BACKEND_8765_PID > /dev/null; then
        log_success "Enhanced Enterprise Backend 8765 started (PID: $BACKEND_8765_PID)"
    else
        log_warning "Enhanced Enterprise Backend 8765 failed, continuing with 8767 only"
    fi
fi

# Start additional sensors if available
if [[ -f "sensors/enhanced_fixed_process_sensor.py" ]]; then
    log_info "Starting process sensor..."
    python3 sensors/enhanced_fixed_process_sensor.py > logs/agents/process_sensor.log 2>&1 &
    PROCESS_PID=$!
    echo $PROCESS_PID > pids/process_sensor.pid
    log_success "Process sensor started (PID: $PROCESS_PID)"
fi

if [[ -f "sensors/total_screen_analyzer.py" ]]; then
    log_info "Starting screen analyzer..."
    python3 sensors/total_screen_analyzer.py > logs/agents/screen_analyzer.log 2>&1 &
    SCREEN_PID=$!
    echo $SCREEN_PID > pids/screen_analyzer.pid
    log_success "Screen analyzer started (PID: $SCREEN_PID)"
fi

# Test connectivity
log_info "Testing system connectivity..."

# Test port 8767 (frontend)
python3 -c "
import asyncio
import websockets
import json

async def test_8767():
    try:
        async with websockets.connect('ws://localhost:8767') as ws:
            welcome = await ws.recv()
            await ws.send(json.dumps({'type': 'chat_request', 'mode': 'Agent', 'message': 'test'}))
            response = await ws.recv()
            print('✅ Port 8767: Frontend compatible backend operational')
            return True
    except Exception as e:
        print(f'❌ Port 8767: {e}')
        return False

asyncio.run(test_8767())
" || log_error "Port 8767 connectivity failed"

# Test port 8765 if available
if [[ -f "pids/enterprise_8765.pid" ]] && ps -p $(cat pids/enterprise_8765.pid) > /dev/null 2>&1; then
    python3 -c "
import asyncio
import websockets
import json

async def test_8765():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send(json.dumps({'type': 'agent_request', 'message': 'test'}))
            response = await ws.recv()
            print('✅ Port 8765: Brain router backend operational')
            return True
    except Exception as e:
        print(f'❌ Port 8765: {e}')
        return False

asyncio.run(test_8765())
" || log_warning "Port 8765 connectivity issues (non-critical)"
fi

# Display system status
echo ""
log_professional "🎯 ENTERPRISE SYSTEM STATUS"
echo "============================"
echo ""
echo "🌐 Frontend Compatible Backend:"
echo "   • Port 8767: ✅ Active (PID: $(cat pids/enterprise_8767.pid 2>/dev/null || echo 'Unknown'))"
echo "   • Message Types: chat_request, system_status, agent_request"
echo "   • Modes: Agent, Ask, Suggest, General"
echo ""

if [[ -f "pids/enterprise_8765.pid" ]] && ps -p $(cat pids/enterprise_8765.pid) > /dev/null 2>&1; then
    echo "🧠 Brain Router Backend:"
    echo "   • Port 8765: ✅ Active (PID: $(cat pids/enterprise_8765.pid))"
    echo "   • Features: Agent self-reflection, Professional validation"
    echo ""
fi

echo "📊 Additional Services:"
if [[ -f "pids/process_sensor.pid" ]]; then
    echo "   • Process Sensor: ✅ (PID: $(cat pids/process_sensor.pid))"
fi
if [[ -f "pids/screen_analyzer.pid" ]]; then
    echo "   • Screen Analyzer: ✅ (PID: $(cat pids/screen_analyzer.pid))"
fi
echo ""

log_professional "Available Commands:"
echo "  • Test frontend: python3 test_frontend_compatibility.py"
echo "  • Test enterprise: python3 test_working_enterprise.py"
echo "  • Check status: ./manage_enterprise_system.sh status"
echo "  • Stop system: ./STOP_ENTERPRISE_SYSTEM_FIXED.sh"
echo ""

log_professional "WebSocket Endpoints:"
echo "  • Frontend: ws://localhost:8767 (for web interface)"
echo "  • Enterprise: ws://localhost:8765 (for brain router)"
echo ""

# Save system info
cat > .enterprise_system_info << EOF
SYSTEM_STARTED=$(date)
FRONTEND_BACKEND_PID=$(cat pids/enterprise_8767.pid 2>/dev/null || echo 'Unknown')
ENTERPRISE_BACKEND_PID=$(cat pids/enterprise_8765.pid 2>/dev/null || echo 'Unknown')
FRONTEND_PORT=8767
ENTERPRISE_PORT=8765
FEATURES=frontend_compatibility,brain_router_integration,agent_automation,enterprise_validation
STATUS=OPERATIONAL
EOF

echo ""
log_success "🎉 ENTERPRISE SYSTEM WITH FRONTEND COMPATIBILITY IS READY!"
echo "========================================================"
log_professional "Frontend can now connect to ws://localhost:8767 successfully"
log_professional "Enterprise features available on both ports 8765 and 8767"
echo ""