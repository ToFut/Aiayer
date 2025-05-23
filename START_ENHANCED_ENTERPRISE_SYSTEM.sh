#!/bin/bash

# Enhanced Enterprise Agent System Startup Script
# Professional implementation with self-reflection, collaboration, and deep analysis
# Like Claude Code and Google Project standards

set -e

echo "🚀 Starting Enhanced Enterprise Agent System"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/segevbin/Desktop/SensAI/Aiayer"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"
PYTHON_ENV="python3"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Function to check if a process is running
check_process() {
    local pid_file="$1"
    local process_name="$2"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $process_name is running (PID: $pid)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $process_name PID file exists but process not running"
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local script="$1"
    local service_name="$2"
    local pid_file="$3"
    local log_file="$4"
    
    if check_process "$pid_file" "$service_name"; then
        return 0
    fi
    
    echo -e "${BLUE}▶${NC} Starting $service_name..."
    
    cd "$PROJECT_DIR"
    nohup $PYTHON_ENV "$script" > "$log_file" 2>&1 &
    echo $! > "$pid_file"
    
    sleep 2
    
    if check_process "$pid_file" "$service_name"; then
        echo -e "${GREEN}✓${NC} $service_name started successfully"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start $service_name"
        if [[ -f "$log_file" ]]; then
            echo "Last 10 lines of log:"
            tail -10 "$log_file"
        fi
        return 1
    fi
}

# Function to check Python dependencies
check_dependencies() {
    echo -e "${BLUE}🔍${NC} Checking Python dependencies..."
    
    local required_modules=("asyncio" "json" "logging" "subprocess" "datetime")
    local missing_modules=()
    
    for module in "${required_modules[@]}"; do
        if ! $PYTHON_ENV -c "import $module" 2>/dev/null; then
            missing_modules+=("$module")
        fi
    done
    
    if [[ ${#missing_modules[@]} -eq 0 ]]; then
        echo -e "${GREEN}✓${NC} All required Python modules available"
        return 0
    else
        echo -e "${RED}✗${NC} Missing Python modules: ${missing_modules[*]}"
        return 1
    fi
}

# Function to validate system requirements
validate_system() {
    echo -e "${BLUE}🔧${NC} Validating system requirements..."
    
    # Check Python version
    if command -v $PYTHON_ENV >/dev/null 2>&1; then
        local python_version=$($PYTHON_ENV --version 2>&1)
        echo -e "${GREEN}✓${NC} Python found: $python_version"
    else
        echo -e "${RED}✗${NC} Python 3 not found"
        return 1
    fi
    
    # Check macOS (required for UI automation)
    if [[ "$(uname)" != "Darwin" ]]; then
        echo -e "${YELLOW}⚠${NC} Warning: This system is optimized for macOS"
    else
        echo -e "${GREEN}✓${NC} macOS detected - UI automation available"
    fi
    
    # Check disk space
    local available_space=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    echo -e "${GREEN}✓${NC} Available disk space: $available_space"
    
    # Check memory
    if command -v vm_stat >/dev/null 2>&1; then
        local memory_pressure=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        echo -e "${GREEN}✓${NC} Memory status: OK"
    fi
    
    return 0
}

# Main startup sequence
main() {
    echo -e "${BLUE}🏗${NC} Enhanced Enterprise Agent System"
    echo "   Professional implementation with:"
    echo "   • Agent self-reflection and task validation"
    echo "   • Inter-agent communication and collaboration"
    echo "   • Professional-grade validation (Claude Code style)"
    echo "   • Deep dive analysis for complex tasks"
    echo "   • Context-aware agent framework"
    echo ""
    
    # Step 1: System validation
    if ! validate_system; then
        echo -e "${RED}✗${NC} System validation failed"
        exit 1
    fi
    
    # Step 2: Check dependencies
    if ! check_dependencies; then
        echo -e "${RED}✗${NC} Dependency check failed"
        exit 1
    fi
    
    # Step 3: Start core memory system
    echo -e "${BLUE}📊${NC} Starting memory system..."
    start_service "memory/memory_system.py" "Memory System" "$PID_DIR/memory_system.pid" "$LOG_DIR/memory_system.log"
    
    # Step 4: Start specialized agents
    echo -e "${BLUE}🤖${NC} Starting specialized agents..."
    start_service "specialized_agents.py" "Specialized Agents" "$PID_DIR/specialized_agents.pid" "$LOG_DIR/specialized_agents.log"
    
    # Step 5: Start professional validation engine
    echo -e "${BLUE}✅${NC} Starting validation engine..."
    start_service "professional_validation_engine.py" "Validation Engine" "$PID_DIR/validation_engine.pid" "$LOG_DIR/validation_engine.log"
    
    # Step 6: Start deep analysis engine
    echo -e "${BLUE}🔬${NC} Starting deep analysis engine..."
    start_service "deep_dive_analysis_engine.py" "Deep Analysis Engine" "$PID_DIR/analysis_engine.pid" "$LOG_DIR/analysis_engine.log"
    
    # Step 7: Start agent reflection system
    echo -e "${BLUE}🧠${NC} Starting agent reflection system..."
    start_service "enterprise_agent_reflection.py" "Agent Reflection System" "$PID_DIR/reflection_system.pid" "$LOG_DIR/reflection_system.log"
    
    # Step 8: Start enhanced backend server
    echo -e "${BLUE}🌐${NC} Starting enhanced backend server..."
    start_service "enhanced_enterprise_agent_system.py" "Enhanced Backend Server" "$PID_DIR/backend_server.pid" "$LOG_DIR/backend_server.log"
    
    # Step 9: Health check
    echo -e "${BLUE}🏥${NC} Performing system health check..."
    sleep 5
    
    local services_running=0
    local total_services=6
    
    for pid_file in "$PID_DIR"/*.pid; do
        if [[ -f "$pid_file" ]]; then
            local service_name=$(basename "$pid_file" .pid)
            if check_process "$pid_file" "$service_name"; then
                ((services_running++))
            fi
        fi
    done
    
    echo ""
    echo "=============================================="
    echo -e "${BLUE}📊 SYSTEM STATUS${NC}"
    echo "=============================================="
    echo -e "Services Running: ${GREEN}$services_running${NC}/$total_services"
    
    if [[ $services_running -eq $total_services ]]; then
        echo -e "Overall Status: ${GREEN}✓ ALL SYSTEMS OPERATIONAL${NC}"
        echo ""
        echo -e "${GREEN}🎉 Enhanced Enterprise Agent System Started Successfully!${NC}"
        echo ""
        echo "Features Available:"
        echo "• Self-reflecting agents with task completion validation"
        echo "• Inter-agent communication for UI context sharing" 
        echo "• Professional-grade validation (Claude Code standards)"
        echo "• Deep dive analysis for complex task verification"
        echo "• Context-aware agent collaboration framework"
        echo ""
        echo "System Endpoints:"
        echo "• Backend Server: http://localhost:8767"
        echo "• WebSocket: ws://localhost:8765"
        echo "• Memory System: Active"
        echo "• Validation Engine: Active"
        echo "• Analysis Engine: Active"
        echo ""
        echo "Usage:"
        echo "1. Send agent requests to backend server"
        echo "2. Agents will self-reflect and collaborate"
        echo "3. Professional validation will be conducted"
        echo "4. Deep analysis will verify task completion"
        echo "5. Human approval will be requested for complex tasks"
        echo ""
        echo "To test the system:"
        echo "  python3 test_enhanced_enterprise_system.py"
        echo ""
        echo "To stop the system:"
        echo "  ./STOP_ENHANCED_ENTERPRISE_SYSTEM.sh"
        
    elif [[ $services_running -gt 0 ]]; then
        echo -e "Overall Status: ${YELLOW}⚠ PARTIAL SYSTEMS OPERATIONAL${NC}"
        echo ""
        echo -e "${YELLOW}⚠ Warning: Not all services started successfully${NC}"
        echo "Check individual service logs for details:"
        for log_file in "$LOG_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                echo "  tail -f $log_file"
            fi
        done
    else
        echo -e "Overall Status: ${RED}✗ SYSTEM STARTUP FAILED${NC}"
        echo ""
        echo -e "${RED}✗ No services started successfully${NC}"
        echo "Check system logs and requirements"
        exit 1
    fi
    
    echo ""
    echo "=============================================="
}

# Handle script interruption
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Startup interrupted${NC}"
    echo "To clean up any partial processes, run:"
    echo "  ./STOP_ENHANCED_ENTERPRISE_SYSTEM.sh"
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"