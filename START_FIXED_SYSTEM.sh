#!/bin/bash

# ========================================================
# 🌟 SensAI FIXED SYSTEM STARTUP 🌟
# 
# Complete intelligent system with:
# - Real LLM Integration (no more mock responses)
# - Enhanced UI Detection & Agent Automation
# - Real-time memory updates & semantic search
# - Multi-mode AI with proper timeout handling
# ========================================================

# ANSI Color codes for beautiful terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

# Display banner
printf "${BOLD}${MAGENTA}"
printf "  ███████╗███████╗███╗   ██╗███████╗ █████╗ ██╗\n"
printf "  ██╔════╝██╔════╝████╗  ██║██╔════╝██╔══██╗██║\n"
printf "  ███████╗█████╗  ██╔██╗ ██║███████╗███████║██║\n"
printf "  ╚════██║██╔══╝  ██║╚██╗██║╚════██║██╔══██║██║\n"
printf "  ███████║███████╗██║ ╚████║███████║██║  ██║██║\n"
printf "  ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝\n"
printf "${RESET}${CYAN} FIXED SYSTEM LAUNCHER - REAL LLM INTEGRATION ${RESET}\n"
printf "\n"

# Navigate to project directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create necessary directories
printf "${YELLOW}📁 Creating required directories...${RESET}\n"
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p logs/llm
mkdir -p logs/ui_detection
mkdir -p logs/do_button
mkdir -p logs/websocket
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/ui_detection
mkdir -p cache/llava_processor
mkdir -p cache/total_screen_analyzer
mkdir -p memory

# Initialize status variables
NEURAL_UI_OK=false
DO_BUTTON_OK=false
BACKEND_OK=false
MEMORY_OK=false
PROCESS_SENSOR_OK=false
SCREEN_SENSOR_OK=false
LLM_OK=false
OLLAMA_OK=false

# Clean up any running processes
printf "${YELLOW}🧹 Cleaning up existing processes...${RESET}\n"
# Cleanup ports
for PORT in 8000 8765 8766 8767 8768; do
    if lsof -i :$PORT > /dev/null 2>&1; then
        printf "   ${RED}→ Port $PORT is in use! Clearing...${RESET}\n"
        lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done

# Kill specific processes if they exist
for PROC in "neural_ui_detector" "universal_intelligent_automation_handler" "enhanced_enterprise_backend" "total_screen_analyzer" "process_sensor" "smart_memory_feeder" "direct_coordinate_automation" "llava_visual_processor"; do
    if pgrep -f "$PROC" > /dev/null; then
        printf "   ${RED}→ Stopping existing $PROC process...${RESET}\n"
        pkill -f "$PROC" 2>/dev/null || true
    fi
done

# Clean log files
> logs/backend/enhanced_enterprise_8767_context.log
> logs/sensors/process_sensor.log
> logs/memory/smart_feeder.log
> logs/ui_detection/neural_ui_detector.log
> logs/do_button/do_button_server.log
> logs/llm/llava_processor.log
> logs/websocket/direct_coordinate_automation.log

# Step 1: Check Ollama LLM Service
printf "\n${GREEN}🧠 Checking Ollama LLM Service...${RESET}\n"
if curl -s http://localhost:11434/api/tags >/dev/null; then
    printf "   ${GREEN}✅ Ollama is running${RESET}\n"
    OLLAMA_OK=true
    
    # Check if llama3.2:1b model is available
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:1b"; then
        printf "   ${GREEN}✅ llama3.2:1b model found${RESET}\n"
        LLM_OK=true
    else
        printf "   ${YELLOW}⚠️ llama3.2:1b model not found. Attempting to pull...${RESET}\n"
        if command -v ollama >/dev/null; then
            ollama pull llama3.2:1b &
            printf "   ${YELLOW}→ Pulling llama3.2:1b in background. This might take a while...${RESET}\n"
            printf "   ${YELLOW}→ System will continue, but LLM responses may be delayed${RESET}\n"
            LLM_OK=true
        else
            printf "   ${RED}❌ ollama command not found. Please install Ollama and pull llama3.2:1b model${RESET}\n"
            printf "   ${YELLOW}→ System will continue with potential fallbacks${RESET}\n"
        fi
    fi
else
    printf "   ${RED}❌ Ollama is not running!${RESET}\n"
    
    # Try to start Ollama (macOS specific)
    if [ -d "/Applications/Ollama.app" ]; then
        printf "   ${YELLOW}→ Attempting to start Ollama...${RESET}\n"
        open /Applications/Ollama.app
        
        # Wait for Ollama to start
        for i in {1..5}; do
            sleep 2
            if curl -s http://localhost:11434/api/tags >/dev/null; then
                printf "   ${GREEN}✅ Ollama started successfully${RESET}\n"
                OLLAMA_OK=true
                LLM_OK=true
                break
            fi
            printf "."
        done
    else
        printf "   ${RED}❌ Ollama not found. Please install Ollama and make sure it's running${RESET}\n"
        printf "   ${YELLOW}→ System will continue with potential fallbacks${RESET}\n"
    fi
fi

# Step 2: Start Direct Coordinate Automation Server
printf "\n${GREEN}🖱️ Starting Direct Coordinate Automation Server on port 8765...${RESET}\n"

# Verify input controller dependencies
printf "   ${YELLOW}→ Verifying input controller dependencies...${RESET}\n"
if ! python3 -c "import pyautogui, pynput" 2>/dev/null; then
    printf "   ${YELLOW}→ Installing required input controller dependencies...${RESET}\n"
    pip3 install pyautogui pynput
fi

# Test input controller
printf "   ${YELLOW}→ Testing input controller...${RESET}\n"
if python3 -c "
import sys
sys.path.append('.')
try:
    from agent_workflow.input_controller import InputController
    controller = InputController()
    print(' Input controller initialized successfully')
    controller.stop()
    sys.exit(0)
except Exception as e:
    print(f' Input controller test failed: {str(e)}')
    sys.exit(1)
" 2>/dev/null; then
    printf "   ${GREEN}✅ Input controller verified${RESET}\n"
else
    printf "   ${RED}❌ Input controller test failed${RESET}\n"
    printf "   ${RED}⚠️ This is required for automation - continuing but some features may not work${RESET}\n"
fi

# Start the direct coordinate automation server
python3 direct_coordinate_automation.py > logs/websocket/direct_coordinate_automation.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/direct_coordinate_automation.pid
printf "   ${BLUE}→ Direct Coordinate Automation Server PID: %d${RESET}\n" "$DO_BUTTON_PID"

# Wait for the server to start
sleep 3
if lsof -i :8765 > /dev/null 2>&1; then
    printf "   ${GREEN}✅ Direct Coordinate Automation Server is listening on port 8765${RESET}\n"
    DO_BUTTON_OK=true
else
    printf "   ${RED}❌ Failed to start Direct Coordinate Automation Server${RESET}\n"
    printf "   ${YELLOW}→ Check logs: logs/websocket/direct_coordinate_automation.log${RESET}\n"
    printf "   ${YELLOW}→ Continuing without DO Button server - some features may not work${RESET}\n"
fi

# Step 3: Start Enhanced Enterprise Backend
printf "\n${GREEN}🚀 Starting Enhanced Enterprise Backend on port 8767...${RESET}\n"

# Ensure port 8767 is free
if lsof -i :8767 > /dev/null 2>&1; then
    printf "   ${RED}→ Port 8767 is in use! Killing process...${RESET}\n"
    lsof -ti :8767 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Fix any type errors in backend
printf "   ${YELLOW}→ Fixing type annotation in backend...${RESET}\n"
sed -i.typeerror.bak 's/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional\[str\] = None) -> List\[Dict\]:/async def _search_memory(self, query: str, top_k: int = 5, application_context: Optional[str] = None) -> List[Dict[str, Any]]:/' enhanced_enterprise_backend_with_context.py 2>/dev/null || true

# Add missing List import if needed
if ! grep -q "from typing import.*List" enhanced_enterprise_backend_with_context.py; then
    sed -i.import.bak 's/from typing import Dict, Any, Set, Optional, Tuple/from typing import Dict, Any, Set, Optional, Tuple, List/' enhanced_enterprise_backend_with_context.py 2>/dev/null || true
fi

# Start the enhanced enterprise backend
python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767_context.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/enhanced_enterprise_backend.pid
printf "   ${BLUE}→ Enhanced Enterprise Backend PID: %d${RESET}\n" "$BACKEND_PID"

# Wait for backend to start
printf "   ${YELLOW}→ Waiting for backend to initialize...${RESET}\n"
for i in {1..10}; do
    if lsof -i :8767 > /dev/null 2>&1; then
        printf "   ${GREEN}✅ Enhanced Enterprise Backend is running on port 8767${RESET}\n"
        BACKEND_OK=true
        break
    fi
    printf "."
    sleep 2
done

if ! $BACKEND_OK; then
    printf "   ${RED}❌ Enhanced Enterprise Backend failed to start${RESET}\n"
    printf "   ${YELLOW}→ Check logs: logs/backend/enhanced_enterprise_8767_context.log${RESET}\n"
    printf "   ${RED}⚠️ This is required for the system - exiting${RESET}\n"
    exit 1
fi

# Step 4: Start Sensor Systems
if $BACKEND_OK; then
    printf "\n${GREEN}📊 Starting Sensor Systems...${RESET}\n"
    
    # Start Process Sensor
    printf "   ${YELLOW}→ Starting Enhanced Process Sensor...${RESET}\n"
    if [ -f "sensors/enhanced_fixed_process_sensor.py" ]; then
        python3 sensors/enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
        PROCESS_PID=$!
        echo $PROCESS_PID > pids/process_sensor.pid
        printf "   ${BLUE}→ Process Sensor PID: %d${RESET}\n" "$PROCESS_PID"
        PROCESS_SENSOR_OK=true
    else
        # Try other versions
        if [ -f "enhanced_fixed_process_sensor.py" ]; then
            python3 enhanced_fixed_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
            PROCESS_PID=$!
            echo $PROCESS_PID > pids/process_sensor.pid
            printf "   ${BLUE}→ Process Sensor PID: %d${RESET}\n" "$PROCESS_PID"
            PROCESS_SENSOR_OK=true
        elif [ -f "process_sensor.py" ]; then
            python3 process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
            PROCESS_PID=$!
            echo $PROCESS_PID > pids/process_sensor.pid
            printf "   ${BLUE}→ Process Sensor PID: %d${RESET}\n" "$PROCESS_PID"
            PROCESS_SENSOR_OK=true
        else
            printf "   ${RED}❌ Process Sensor file not found${RESET}\n"
        fi
    fi
    
    # Start Total Screen Analyzer
    printf "   ${YELLOW}→ Starting Total Screen Analyzer...${RESET}\n"
    if [ -f "sensors/total_screen_analyzer.py" ]; then
        python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
        SCREEN_PID=$!
        echo $SCREEN_PID > pids/total_screen_analyzer.pid
        printf "   ${BLUE}→ Total Screen Analyzer PID: %d${RESET}\n" "$SCREEN_PID"
        SCREEN_SENSOR_OK=true
    else
        # Try other versions
        if [ -f "total_screen_analyzer.py" ]; then
            python3 total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
            SCREEN_PID=$!
            echo $SCREEN_PID > pids/total_screen_analyzer.pid
            printf "   ${BLUE}→ Total Screen Analyzer PID: %d${RESET}\n" "$SCREEN_PID"
            SCREEN_SENSOR_OK=true
        else
            printf "   ${YELLOW}⚠️ Total Screen Analyzer file not found, continuing without it${RESET}\n"
        fi
    fi
    
    # Start LLaVA Visual Processor if available
    printf "   ${YELLOW}→ Checking for LLaVA Visual Processor...${RESET}\n"
    if [ -f "sensors/llava_visual_processor.py" ]; then
        printf "   ${YELLOW}→ Starting LLaVA Visual Processor...${RESET}\n"
        python3 sensors/llava_visual_processor.py > logs/llm/llava_processor.log 2>&1 &
        LLAVA_PID=$!
        echo $LLAVA_PID > pids/llava_processor.pid
        printf "   ${BLUE}→ LLaVA Visual Processor PID: %d${RESET}\n" "$LLAVA_PID"
    elif [ -f "llava_visual_processor.py" ]; then
        printf "   ${YELLOW}→ Starting LLaVA Visual Processor...${RESET}\n"
        python3 llava_visual_processor.py > logs/llm/llava_processor.log 2>&1 &
        LLAVA_PID=$!
        echo $LLAVA_PID > pids/llava_processor.pid
        printf "   ${BLUE}→ LLaVA Visual Processor PID: %d${RESET}\n" "$LLAVA_PID"
    else
        printf "   ${YELLOW}⚠️ LLaVA Visual Processor not found, continuing without it${RESET}\n"
    fi
    
    # Start Memory Integration if available
    printf "   ${YELLOW}→ Checking for Smart Memory Feeder...${RESET}\n"
    if [ -f "smart_memory_feeder.py" ]; then
        printf "   ${YELLOW}→ Starting Smart Memory Feeder...${RESET}\n"
        python3 smart_memory_feeder.py > logs/memory/smart_feeder.log 2>&1 &
        MEMORY_PID=$!
        echo $MEMORY_PID > pids/memory_feeder.pid
        printf "   ${BLUE}→ Smart Memory Feeder PID: %d${RESET}\n" "$MEMORY_PID"
        MEMORY_OK=true
    else
        printf "   ${YELLOW}⚠️ Smart Memory Feeder not found, continuing without it${RESET}\n"
        printf "   ${YELLOW}→ Backend has built-in memory system, so this is optional${RESET}\n"
    fi
    
    # Wait for sensors to initialize
    printf "   ${YELLOW}→ Waiting for sensors to initialize...${RESET}\n"
    sleep 5
fi

# Create stop script
printf "\n${YELLOW}📝 Creating stop script...${RESET}\n"
cat > STOP_FIXED_SYSTEM.sh << 'EOF'
#!/bin/bash

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

printf "${BOLD}${RED}⚠️ STOPPING SENSAI SYSTEM...${RESET}\n"

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            printf "${YELLOW}→ Stopping %s (PID: %d)${RESET}\n" "$COMPONENT" "$PID"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
printf "→ Cleaning up remaining processes...${RESET}\n"
pkill -f "neural_ui_detector" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
pkill -f "enhanced_enterprise_backend" 2>/dev/null || true
pkill -f "smart_memory_feeder" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true
pkill -f "total_screen_analyzer" 2>/dev/null || true
pkill -f "llava_visual_processor" 2>/dev/null || true
pkill -f "python3 -m http.server 8000" 2>/dev/null || true

# Clean up ports
printf "→ Freeing used ports...${RESET}\n"
for PORT in 8000 8765 8766 8767 8768; do
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
done

printf "${GREEN}✅ SENSAI SYSTEM STOPPED${RESET}\n"
EOF

chmod +x STOP_FIXED_SYSTEM.sh

# System status summary
printf "\n${BOLD}${MAGENTA}=============================================${RESET}\n"
printf "${BOLD}${MAGENTA}      SENSAI FIXED SYSTEM READY!      ${RESET}\n"
printf "${BOLD}${MAGENTA}=============================================${RESET}\n"
printf "\n"
printf "${CYAN}🌐 System Components:${RESET}\n"
printf "   ${GREEN}✅ Enhanced Enterprise Backend:${RESET} ws://localhost:8767\n"

if $OLLAMA_OK; then
    printf "   ${GREEN}✅ Ollama LLM Service:${RESET} http://localhost:11434\n"
    if $LLM_OK; then
        printf "   ${GREEN}✅ LLM Model:${RESET} llama3.2:1b\n"
    else
        printf "   ${YELLOW}⚠️ LLM Model: Loading llama3.2:1b in background${RESET}\n"
    fi
else
    printf "   ${RED}❌ Ollama LLM Service: INACTIVE${RESET}\n"
    printf "   ${YELLOW}→ System will use fallbacks for responses${RESET}\n"
fi

if [ "$DO_BUTTON_OK" = true ]; then
    printf "   ${GREEN}✅ DO Button Server:${RESET} ws://localhost:8765\n"
else
    printf "   ${YELLOW}⚠️ DO Button Server: INACTIVE${RESET}\n"
fi

if $PROCESS_SENSOR_OK; then
    printf "   ${GREEN}✅ Process Sensor:${RESET} Active (PID: %d)\n" "$PROCESS_PID"
else
    printf "   ${RED}❌ Process Sensor: FAILED${RESET}\n"
fi

if $SCREEN_SENSOR_OK; then
    printf "   ${GREEN}✅ Total Screen Analyzer:${RESET} Active (PID: %d)\n" "$SCREEN_PID"
else
    printf "   ${YELLOW}⚠️ Total Screen Analyzer: INACTIVE${RESET}\n"
fi

if [ ! -z "$LLAVA_PID" ] && ps -p $LLAVA_PID > /dev/null; then
    printf "   ${GREEN}✅ LLaVA Visual Processor:${RESET} Active (PID: %d)\n" "$LLAVA_PID"
else
    printf "   ${YELLOW}⚠️ LLaVA Visual Processor: INACTIVE${RESET}\n"
fi

if $MEMORY_OK; then
    printf "   ${GREEN}✅ Smart Memory Feeder:${RESET} Active (PID: %d)\n" "$MEMORY_PID"
else
    printf "   ${YELLOW}⚠️ Smart Memory Feeder: INACTIVE${RESET}\n"
    printf "   ${YELLOW}→ Using backend's built-in memory system${RESET}\n"
fi

printf "\n"
printf "${YELLOW}🚀 System Capabilities:${RESET}\n"
printf "   ${BLUE}→ Agent Mode:${RESET} Real UI automation with coordinate control\n"
printf "   ${BLUE}→ Ask Mode:${RESET} Context-aware answers with REAL LLM integration\n"
printf "   ${BLUE}→ Suggest Mode:${RESET} Proactive suggestions based on memory patterns\n"
printf "   ${BLUE}→ General Mode:${RESET} Conversational memory with context integration\n"
printf "\n"
printf "${YELLOW}⚡ LLM Integration:${RESET}\n"
printf "   ${BLUE}→ Model:${RESET} llama3.2:1b\n"
printf "   ${BLUE}→ Fixed Timeout Handling:${RESET} Proper error recovery for timeouts\n"
printf "   ${BLUE}→ NDJSON Streaming Support:${RESET} Enhanced response handling\n"
printf "   ${BLUE}→ Intelligent Fallbacks:${RESET} Graceful degradation if LLM fails\n"
printf "   ${BLUE}→ Memory Integration:${RESET} Contextual response enhancement\n"
printf "\n"
printf "${YELLOW}🔧 System Management:${RESET}\n"
printf "   ${BLUE}→ Stop System:${RESET} ./STOP_FIXED_SYSTEM.sh\n"
printf "   ${BLUE}→ View Backend Logs:${RESET} tail -f logs/backend/enhanced_enterprise_8767_context.log\n"
printf "   ${BLUE}→ View DO Button Logs:${RESET} tail -f logs/websocket/direct_coordinate_automation.log\n"
printf "   ${BLUE}→ View Memory Logs:${RESET} tail -f logs/memory/smart_feeder.log\n"
printf "\n"

# Create a symlink to the main START.sh script for easy access
ln -sf START_FIXED_SYSTEM.sh START.sh

# Show backend logs
printf "${BOLD}${GREEN}🎯 System is ready for use! Showing backend logs...${RESET}\n"
printf "\n"

# Show live logs from backend
tail -f logs/backend/enhanced_enterprise_8767_context.log | sed 's/^/[BACKEND] /'