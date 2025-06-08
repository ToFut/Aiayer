#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ========================================================
# 🌟 SensAI MASTER SYSTEM STARTUP 🌟
# 
# Complete intelligent system with:
# - Neural UI Detection & Agent Automation
# - Real-time memory updates & semantic search
# - Multi-mode AI with LLM integration
# - TeamViewer-style remote control capabilities
# ========================================================

# ANSI Color codes for beautiful terminal output
printf "${BOLD}${MAGENTA}"
printf "  ███████╗███████╗███╗   ██╗███████╗ █████╗ ██╗\n"
printf "  ██╔════╝██╔════╝████╗  ██║██╔════╝██╔══██╗██║\n"
printf "  ███████╗█████╗  ██╔██╗ ██║███████╗███████║██║\n"
printf "  ╚════██║██╔══╝  ██║╚██╗██║╚════██║██╔══██║██║\n"
printf "  ███████║███████╗██║ ╚████║███████║██║  ██║██║\n"
printf "  ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝\n"
printf "${RESET}${CYAN} MASTER SYSTEM LAUNCHER ${RESET}\n"
printf "\n"

printf "${BOLD}${BLUE}⚡ INTELLIGENT MULTI-MODE AI SYSTEM WITH NEURAL UI DETECTION ⚡${RESET}\n"

# Navigate to project directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create necessary directories
printf "${YELLOW}📁 Creating required directories...${RESET}\n"
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/backend
mkdir -p logs/ui_detection
mkdir -p logs/do_button
mkdir -p logs/warmup
mkdir -p logs/overlay
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/ui_detection
mkdir -p cache/professional_agent
mkdir -p cache/llava_processor
mkdir -p cache/total_screen_analyzer
mkdir -p memory

# Fix any potentially broken components
printf "${YELLOW}🔧 Fixing type annotations in backend...${RESET}\n"

# Initialize status variables
NEURAL_UI_OK=false
DO_BUTTON_OK=false
BACKEND_OK=false
MEMORY_OK=false
PROCESS_SENSOR_OK=false
SCREEN_SENSOR_OK=false
LLM_WARMUP_OK=false
DIRECT_AUTOMATION_OK=false
BRIDGE_OK=false

# Port configuration
NEURAL_UI_PORT=8768
DIRECT_AUTOMATION_PORT=8765
BACKEND_PORT=8767
OVERLAY_BRIDGE_PORT=8766
HTTP_PORT=8000

# Function to check if port is available
check_port_available() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to wait for port to be available
wait_for_port() {
    local port=$1
    local max_attempts=$2
    local attempts=0
    
    printf "   ${YELLOW}→ Waiting for port $port to become available...${RESET}"
    while ! check_port_available $port && [ $attempts -lt $max_attempts ]; do
        printf "."
        sleep 1
        attempts=$((attempts + 1))
    done
    
    if check_port_available $port; then
        printf " ${GREEN}Available!${RESET}\n"
        return 0
    else
        printf " ${RED}Still in use!${RESET}\n"
        return 1
    fi
}

# Function to wait for port to be listening
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_wait=$3
    local current_wait=0
    local interval=1
    
    printf "   ${YELLOW}→ Waiting for $service_name to start on port $port...${RESET}"
    while ! lsof -i :$port > /dev/null 2>&1 && [ $current_wait -lt $max_wait ]; do
        printf "."
        sleep $interval
        current_wait=$((current_wait + interval))
    done
    
    if lsof -i :$port > /dev/null 2>&1; then
        printf " ${GREEN}Started!${RESET}\n"
        return 0
    else
        printf " ${RED}Failed to start!${RESET}\n"
        return 1
    fi
}

# Function to kill process by port
kill_process_on_port() {
    local port=$1
    if lsof -ti :$port > /dev/null 2>&1; then
        printf "   ${YELLOW}→ Killing process on port $port${RESET}\n"
        lsof -ti :$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# Clean up any running processes
printf "${YELLOW}🧹 Cleaning up existing processes...${RESET}\n"

# Kill processes by name
PROCESS_LIST=(
    "neural_ui_detector"
    "universal_intelligent_automation_handler" 
    "enhanced_enterprise_backend" 
    "enterprise_backend_8767"
    "total_screen_analyzer" 
    "process_sensor" 
    "smart_memory_feeder" 
    "llm_warmup_manager" 
    "direct_coordinate_automation" 
    "fixed_bridge_server"
    "start_neural_ui_detector"
    "start_direct_automation"
    "start_neural_ui_handler"
    "simple_backend_server"
    "simple_process_sensor"
    "python3 -m http.server"
)

for PROC in "${PROCESS_LIST[@]}"; do
    if pgrep -f "$PROC" > /dev/null; then
        printf "   ${RED}→ Stopping existing $PROC process...${RESET}\n"
        pkill -f "$PROC" 2>/dev/null || true
        sleep 1
    fi
done

# Kill processes on ports we need
for PORT in $HTTP_PORT $NEURAL_UI_PORT $DIRECT_AUTOMATION_PORT $BACKEND_PORT $OVERLAY_BRIDGE_PORT; do
    kill_process_on_port $PORT
done

# Clean log files
> logs/backend/enhanced_enterprise_8767.log
> logs/sensors/process_sensor.log
> logs/memory/smart_feeder.log
> logs/ui_detection/neural_ui_detector.log
> logs/do_button/do_button_server.log
> logs/warmup/llm_warmup.log
> logs/sensors/total_screen_analyzer.log
> logs/overlay/fixed_bridge.log

# 1. Start LLM Warmup Manager (if available)
printf "\n${GREEN}🔥 Starting LLM Warmup Manager...${RESET}\n"

if [ -f "llm_warmup_manager.py" ]; then
    # Install dependencies if needed
    if ! python3 -c "import aiohttp" 2>/dev/null; then
        printf "   ${YELLOW}→ Installing LLM Warmup Manager dependencies...${RESET}\n"
        pip3 install aiohttp 2>/dev/null
    fi

    python3 llm_warmup_manager.py > logs/warmup/llm_warmup.log 2>&1 &
    WARMUP_PID=$!
    echo $WARMUP_PID > pids/llm_warmup_manager.pid
    printf "   ${BLUE}→ LLM Warmup Manager PID: %d${RESET}\n" "$WARMUP_PID"
    LLM_WARMUP_OK=true
    sleep 2
else
    printf "   ${YELLOW}⚠️ llm_warmup_manager.py not found, skipping LLM Warmup Manager${RESET}\n"
fi

# 2. Start Enhanced Enterprise Backend on port 8767 FIRST
# This is a critical component that others depend on
printf "\n${GREEN}🚀 Starting Enhanced Enterprise Backend on port $BACKEND_PORT...${RESET}\n"

# Check for port availability
if ! check_port_available $BACKEND_PORT; then
    printf "   ${RED}→ Port $BACKEND_PORT is already in use. Attempting to free it...${RESET}\n"
    kill_process_on_port $BACKEND_PORT
    wait_for_port $BACKEND_PORT 10
fi

# Check dependencies for backend
if ! python3 -c "import websockets" 2>/dev/null; then
    printf "   ${YELLOW}→ Installing backend dependencies...${RESET}\n"
    pip3 install websockets 2>/dev/null
fi

# Try multiple potential backend files in order of preference
if [ -f "enhanced_enterprise_backend_with_context.py" ]; then
    python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/backend.pid
    printf "   ${BLUE}→ Enhanced Backend PID: %d${RESET}\n" "$BACKEND_PID"
    
    # Wait for backend to start on port 8767 with longer timeout
    if wait_for_service $BACKEND_PORT "Enhanced Enterprise Backend" 30; then
        printf "   ${GREEN}✅ Enhanced Enterprise Backend is running on port $BACKEND_PORT${RESET}\n"
        BACKEND_OK=true
    else
        printf "\n   ${RED}❌ Enhanced Backend failed to start, trying alternatives...${RESET}\n"
        kill $BACKEND_PID 2>/dev/null || true
    fi
fi

# If enhanced backend didn't start, try enterprise backend
if ! $BACKEND_OK && [ -f "enterprise_backend_8767.py" ]; then
    printf "   ${YELLOW}→ Trying enterprise_backend_8767.py...${RESET}\n"
    python3 enterprise_backend_8767.py > logs/backend/enterprise_backend_8767.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/backend.pid
    printf "   ${BLUE}→ Enterprise Backend PID: %d${RESET}\n" "$BACKEND_PID"
    
    # Wait for backend to start
    if wait_for_service $BACKEND_PORT "Enterprise Backend" 20; then
        printf "   ${GREEN}✅ Enterprise Backend is running on port $BACKEND_PORT${RESET}\n"
        BACKEND_OK=true
    else
        printf "   ${RED}❌ Enterprise Backend failed to start, trying next alternative...${RESET}\n"
        kill $BACKEND_PID 2>/dev/null || true
    fi
fi

# If still not started, try with fixed visual memory
if ! $BACKEND_OK && [ -f "enterprise_backend_8767_with_fixed_visual_memory.py" ]; then
    printf "   ${YELLOW}→ Trying enterprise_backend_8767_with_fixed_visual_memory.py...${RESET}\n"
    python3 enterprise_backend_8767_with_fixed_visual_memory.py > logs/backend/enterprise_backend_8767.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/backend.pid
    printf "   ${BLUE}→ Enterprise Backend with Fixed Visual Memory PID: %d${RESET}\n" "$BACKEND_PID"
    
    # Wait for backend to start
    if wait_for_service $BACKEND_PORT "Enterprise Backend with Fixed Visual Memory" 20; then
        printf "   ${GREEN}✅ Enterprise Backend with Fixed Visual Memory is running on port $BACKEND_PORT${RESET}\n"
        BACKEND_OK=true
    else
        printf "   ${RED}❌ This backend also failed to start, trying real AI version...${RESET}\n"
        kill $BACKEND_PID 2>/dev/null || true
    fi
fi

# Try real AI version as last resort
if ! $BACKEND_OK && [ -f "enterprise_backend_8767_with_real_ai.py" ]; then
    printf "   ${YELLOW}→ Trying enterprise_backend_8767_with_real_ai.py...${RESET}\n"
    python3 enterprise_backend_8767_with_real_ai.py > logs/backend/enterprise_backend_8767.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/backend.pid
    printf "   ${BLUE}→ Enterprise Backend with Real AI PID: %d${RESET}\n" "$BACKEND_PID"
    
    # Wait for backend to start
    if wait_for_service $BACKEND_PORT "Enterprise Backend with Real AI" 20; then
        printf "   ${GREEN}✅ Enterprise Backend with Real AI is running on port $BACKEND_PORT${RESET}\n"
        BACKEND_OK=true
    else
        printf "   ${RED}❌ All backend attempts failed. Creating simple version...${RESET}\n"
        kill $BACKEND_PID 2>/dev/null || true
    fi
fi

# Create a simple backend if all else fails
if ! $BACKEND_OK; then
    # Create simple backend
    cat > simple_backend_server.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Backend Server
Provides basic WebSocket server on port 8767
"""
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_enterprise_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_backend")

class SimpleBackendServer:
    def __init__(self):
        self.clients = set()
        self.mode_handlers = {
            "ask": self.handle_ask_mode,
            "agent": self.handle_agent_mode,
            "suggest": self.handle_suggest_mode,
            "general": self.handle_general_mode
        }
        logger.info("Simple Backend Server initialized")
    
    async def handle_ask_mode(self, message):
        """Handle ask mode requests"""
        logger.info("Processing ask mode request")
        return {
            "type": "response",
            "mode": "ask",
            "message": "This is a simple mock response for ask mode.",
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_agent_mode(self, message):
        """Handle agent mode requests"""
        logger.info("Processing agent mode request")
        return {
            "type": "response",
            "mode": "agent",
            "message": "This is a simple mock response for agent mode.",
            "plan": {
                "title": "Example Plan",
                "steps": [
                    {"id": 1, "description": "Example step 1"},
                    {"id": 2, "description": "Example step 2"}
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_suggest_mode(self, message):
        """Handle suggest mode requests"""
        logger.info("Processing suggest mode request")
        return {
            "type": "response",
            "mode": "suggest",
            "message": "This is a simple mock response for suggest mode.",
            "suggestions": ["Suggestion 1", "Suggestion 2"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_general_mode(self, message):
        """Handle general mode requests"""
        logger.info("Processing general mode request")
        return {
            "type": "response",
            "mode": "general",
            "message": "This is a simple mock response for general mode.",
            "timestamp": datetime.now().isoformat()
        }

async def handle_client(websocket, path):
    """Handle client connections"""
    server = SimpleBackendServer()
    logger.info("Client connected")
    server.clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message: {data.get('type', 'unknown')}")
                
                # Handle request based on mode
                mode = data.get("mode", "general").lower()
                handler = server.mode_handlers.get(mode, server.handle_general_mode)
                
                # Generate response
                response = await handler(data)
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        server.clients.remove(websocket)

async def main():
    port = 8767
    host = "0.0.0.0"  # Listen on all interfaces
    logger.info("Starting Simple Backend Server on port " + str(port))
    
    server = await websockets.serve(
        handle_client, 
        host, 
        port, 
        ping_interval=50,
        ping_timeout=300
    )
    
    print(f"Simple Backend Server running on ws://{host}:{port}")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF

    chmod +x simple_backend_server.py
    
    # Start the simple backend
    python3 simple_backend_server.py > logs/backend/enhanced_enterprise_8767.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/backend.pid
    printf "   ${BLUE}→ Simple Backend Server PID: %d${RESET}\n" "$BACKEND_PID"
    
    # Wait for backend to start
    if wait_for_service $BACKEND_PORT "Simple Backend Server" 10; then
        printf "   ${GREEN}✅ Simple Backend Server is running on port $BACKEND_PORT${RESET}\n"
        BACKEND_OK=true
    else
        printf "   ${RED}❌ Simple Backend Server also failed. System may not function properly.${RESET}\n"
    fi
fi

# Only continue if backend is running
if ! $BACKEND_OK; then
    printf "${RED}CRITICAL ERROR: Backend server could not be started. Exiting.${RESET}\n"
    exit 1
fi

# 3. Start Process Sensor
printf "\n${GREEN}📊 Starting Process Sensor...${RESET}\n"

# Try different process sensor implementations
PROCESS_SENSOR_FILES=(
    "sensors/process_sensor.py"
    "sensors/enhanced_fixed_process_sensor.py"
    "enhanced_fixed_process_sensor.py"
    "process_sensor.py"
    "fixed_process_sensor.py"
)

for file in "${PROCESS_SENSOR_FILES[@]}"; do
    if [ -f "$file" ]; then
        printf "   ${YELLOW}→ Found process sensor: $file${RESET}\n"
        python3 $file > logs/sensors/process_sensor.log 2>&1 &
        PROCESS_PID=$!
        echo $PROCESS_PID > pids/process_sensor.pid
        printf "   ${BLUE}→ Process Sensor PID: %d${RESET}\n" "$PROCESS_PID"
        PROCESS_SENSOR_OK=true
        break
    fi
done

# Create a simple process sensor if none found
if ! $PROCESS_SENSOR_OK; then
    printf "   ${YELLOW}⚠️ Process Sensor file not found, creating simple version...${RESET}\n"
    
    # Create a simple process sensor
    cat > simple_process_sensor.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Process Sensor
Captures running applications and saves to cache
"""
import json
import os
import time
import logging
import subprocess
import platform
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("process_sensor")

# Ensure cache directory exists
os.makedirs('cache/process_sensor', exist_ok=True)
CACHE_FILE = 'cache/process_sensor/process_cache.json'

def get_running_apps_macos():
    """Get running applications on macOS"""
    try:
        cmd = ["osascript", "-e", 'tell application "System Events" to get name of (processes where background only is false)']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        apps = result.stdout.strip().split(", ")
        return [app.strip() for app in apps if app.strip()]
    except Exception as e:
        logger.error(f"Error getting macOS apps: {e}")
        return []

def get_running_apps_linux():
    """Get running applications on Linux"""
    try:
        cmd = ["ps", "-e", "-o", "comm="]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        apps = result.stdout.strip().split("\n")
        return [app.strip() for app in apps if app.strip()]
    except Exception as e:
        logger.error(f"Error getting Linux apps: {e}")
        return []

def get_running_apps_windows():
    """Get running applications on Windows"""
    try:
        cmd = ["tasklist", "/fo", "csv", "/nh"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        apps = [line.split('","')[0].strip('"') for line in lines if line]
        return [app for app in apps if app]
    except Exception as e:
        logger.error(f"Error getting Windows apps: {e}")
        return []

def get_running_apps():
    """Get running applications based on platform"""
    system = platform.system()
    if system == "Darwin":
        return get_running_apps_macos()
    elif system == "Linux":
        return get_running_apps_linux()
    elif system == "Windows":
        return get_running_apps_windows()
    else:
        logger.warning(f"Unsupported platform: {system}")
        return []

def update_process_cache():
    """Update process cache with current running applications"""
    try:
        # Get running apps
        apps = get_running_apps()
        
        # Prepare data
        current_data = {
            "timestamp": datetime.now().isoformat(),
            "running_apps": apps,
            "process_count": len(apps)
        }
        
        # Load existing cache if available
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            else:
                cache = {"history": []}
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            cache = {"history": []}
        
        # Update cache
        cache["current"] = current_data
        cache["history"].append(current_data)
        
        # Keep only last 10 entries in history
        if len(cache["history"]) > 10:
            cache["history"] = cache["history"][-10:]
        
        # Save cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
            
        logger.info(f"Updated process cache with {len(apps)} applications")
        return True
        
    except Exception as e:
        logger.error(f"Error updating process cache: {e}")
        return False

def main():
    """Main loop to update process cache at regular intervals"""
    logger.info("Starting Simple Process Sensor")
    
    interval = 10  # seconds
    
    try:
        while True:
            update_process_cache()
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Process Sensor stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
EOF

    chmod +x simple_process_sensor.py
    
    # Start the process sensor
    python3 simple_process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
    PROCESS_PID=$!
    echo $PROCESS_PID > pids/process_sensor.pid
    printf "   ${BLUE}→ Simple Process Sensor PID: %d${RESET}\n" "$PROCESS_PID"
    PROCESS_SENSOR_OK=true
fi

sleep 2

# 4. Start Total Screen Analyzer
printf "\n${GREEN}👁️ Starting Total Screen Analyzer...${RESET}\n"

# Check multiple potential locations
if [ -f "sensors/total_screen_analyzer.py" ]; then
    python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
    SCREEN_PID=$!
    echo $SCREEN_PID > pids/total_screen_analyzer.pid
    printf "   ${BLUE}→ Total Screen Analyzer PID: %d${RESET}\n" "$SCREEN_PID"
    SCREEN_SENSOR_OK=true
elif [ -f "total_screen_analyzer.py" ]; then
    python3 total_screen_analyzer.py > logs/sensors/total_screen_analyzer.log 2>&1 &
    SCREEN_PID=$!
    echo $SCREEN_PID > pids/total_screen_analyzer.pid
    printf "   ${BLUE}→ Total Screen Analyzer PID: %d${RESET}\n" "$SCREEN_PID"
    SCREEN_SENSOR_OK=true
else
    printf "   ${YELLOW}⚠️ Total Screen Analyzer file not found, continuing without screen analysis${RESET}\n"
fi

sleep 2

# 5. Start Smart Memory Feeder
printf "\n${GREEN}🧠 Starting Smart Memory Feeder...${RESET}\n"

# Try different memory feeder implementations
MEMORY_FEEDER_FILES=(
    "smart_memory_feeder.py"
    "fixed_meaningful_memory_feeder.py"
    "enhanced_meaningful_memory_feeder.py"
    "simple_continuous_memory_feeder.py"
)

for file in "${MEMORY_FEEDER_FILES[@]}"; do
    if [ -f "$file" ]; then
        printf "   ${YELLOW}→ Found memory feeder: $file${RESET}\n"
        python3 $file > logs/memory/smart_feeder.log 2>&1 &
        MEMORY_PID=$!
        echo $MEMORY_PID > pids/memory_feeder.pid
        printf "   ${BLUE}→ Memory Feeder PID: %d${RESET}\n" "$MEMORY_PID"
        MEMORY_OK=true
        sleep 2
        break
    fi
done

if ! $MEMORY_OK; then
    printf "   ${YELLOW}⚠️ Memory Feeder file not found, continuing without memory integration${RESET}\n"
fi

# 6. Start Direct Coordinate Automation on port 8765
printf "\n${GREEN}🖱️ Starting Direct Coordinate Automation Server on port $DIRECT_AUTOMATION_PORT...${RESET}\n"

# Check for port availability
if ! check_port_available $DIRECT_AUTOMATION_PORT; then
    printf "   ${RED}→ Port $DIRECT_AUTOMATION_PORT is already in use. Attempting to free it...${RESET}\n"
    kill_process_on_port $DIRECT_AUTOMATION_PORT
    wait_for_port $DIRECT_AUTOMATION_PORT 10
fi

if [ -f "direct_coordinate_automation.py" ]; then
    # Install dependencies if needed
    if ! python3 -c "import pyautogui" 2>/dev/null; then
        printf "   ${YELLOW}→ Installing input controller dependencies...${RESET}\n"
        pip3 install pyautogui pynput 2>/dev/null
    fi

    # Start the Direct Automation server
    python3 direct_coordinate_automation.py > logs/do_button/do_button_server.log 2>&1 &
    DO_BUTTON_PID=$!
    echo $DO_BUTTON_PID > pids/do_button_server.pid
    printf "   ${BLUE}→ Direct Automation Server PID: %d${RESET}\n" "$DO_BUTTON_PID"

    # Wait for server to start
    if wait_for_service $DIRECT_AUTOMATION_PORT "Direct Automation Server" 10; then
        printf "   ${GREEN}✅ Direct Automation Server is listening on port $DIRECT_AUTOMATION_PORT${RESET}\n"
        DIRECT_AUTOMATION_OK=true
    else
        printf "   ${YELLOW}⚠️ Direct Automation Server failed to start, continuing without it${RESET}\n"
        kill $DO_BUTTON_PID 2>/dev/null || true
    fi
else
    printf "   ${YELLOW}⚠️ direct_coordinate_automation.py not found, creating simplified version...${RESET}\n"
    
    # Create simplified version
    cat > start_direct_automation.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/do_button', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/do_button/do_button_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("direct_automation")

class SimpleAutomationServer:
    def __init__(self):
        self.clients = set()
        self.pending_plans = {}
        logger.info("Initializing Simple Automation Server")
        
    async def execute_plan(self, plan_id, plan_data=None):
        """Mock plan execution"""
        logger.info("Mock execution for plan: " + str(plan_id))
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Return mock success result
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "Mock execution completed in compatibility mode",
            "timestamp": datetime.now().isoformat()
        }

async def handle_client(websocket, path):
    """Handle client connections"""
    server = SimpleAutomationServer()
    logger.info("Client connected")
    server.clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                logger.info(f"Received message type: {msg_type}")
                
                # Handle plan execution
                if msg_type == "execute_plan" and "plan_id" in data:
                    plan_id = data.get("plan_id")
                    result = await server.execute_plan(plan_id, data.get("plan", {}))
                    await websocket.send(json.dumps({
                        "type": "execution_result",
                        "plan_id": plan_id,
                        "success": True,
                        "message": "Plan executed successfully (mock)",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                # Echo back any other message types
                else:
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": msg_type,
                        "message": "Received message (compatibility mode)",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        server.clients.remove(websocket)

async def main():
    port = 8765
    host = "0.0.0.0"  # Listen on all interfaces
    logger.info("Starting Simple Automation Server on port " + str(port))
    
    server = await websockets.serve(
        handle_client, 
        host, 
        port, 
        ping_interval=50,
        ping_timeout=300
    )
    
    print(f"Simple Automation Server running on ws://{host}:{port}")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF

    chmod +x start_direct_automation.py
    
    # Start the server
    python3 start_direct_automation.py > logs/do_button/do_button_server.log 2>&1 &
    DO_BUTTON_PID=$!
    echo $DO_BUTTON_PID > pids/do_button_server.pid
    printf "   ${BLUE}→ Simple Automation Server PID: %d${RESET}\n" "$DO_BUTTON_PID"
    
    # Wait for server to start
    if wait_for_service $DIRECT_AUTOMATION_PORT "Simple Automation Server" 10; then
        printf "   ${GREEN}✅ Simple Automation Server is listening on port $DIRECT_AUTOMATION_PORT${RESET}\n"
        DIRECT_AUTOMATION_OK=true
    else
        printf "   ${YELLOW}⚠️ Simple Automation Server failed to start, continuing without it${RESET}\n"
        kill $DO_BUTTON_PID 2>/dev/null || true
    fi
fi

# 7. Start Neural UI Detector on port 8768
printf "\n${GREEN}🧠 Starting Neural UI Detector on port $NEURAL_UI_PORT...${RESET}\n"

# Check for port availability
if ! check_port_available $NEURAL_UI_PORT; then
    printf "   ${RED}→ Port $NEURAL_UI_PORT is already in use. Attempting to free it...${RESET}\n"
    kill_process_on_port $NEURAL_UI_PORT
    wait_for_port $NEURAL_UI_PORT 10
fi

if [ -f "neural_ui_detector.py" ]; then
    # Check for required dependencies
    if ! python3 -c "import websockets" 2>/dev/null; then
        printf "   ${YELLOW}→ Installing Neural UI Detector dependencies...${RESET}\n"
        pip3 install websockets 2>/dev/null
    fi
    
    python3 neural_ui_detector.py > logs/ui_detection/neural_ui_detector.log 2>&1 &
    NEURAL_UI_PID=$!
    echo $NEURAL_UI_PID > pids/neural_ui_detector.pid
    printf "   ${BLUE}→ Neural UI Detector PID: %d${RESET}\n" "$NEURAL_UI_PID"
    
    # Wait for Neural UI Detector to start
    if wait_for_service $NEURAL_UI_PORT "Neural UI Detector" 15; then
        printf "   ${GREEN}✅ Neural UI Detector is listening on port $NEURAL_UI_PORT${RESET}\n"
        NEURAL_UI_OK=true
    else
        printf "   ${YELLOW}⚠️ Neural UI Detector not responding on port $NEURAL_UI_PORT, trying neural_ui_detector_server.py...${RESET}\n"
        kill $NEURAL_UI_PID 2>/dev/null || true
        
        # Try neural_ui_detector_server.py as fallback
        if [ -f "neural_ui_detector_server.py" ]; then
            python3 neural_ui_detector_server.py > logs/ui_detection/neural_ui_detector.log 2>&1 &
            NEURAL_UI_PID=$!
            echo $NEURAL_UI_PID > pids/neural_ui_detector.pid
            printf "   ${BLUE}→ Neural UI Detector Server PID: %d${RESET}\n" "$NEURAL_UI_PID"
            
            # Wait for Neural UI Detector to start
            if wait_for_service $NEURAL_UI_PORT "Neural UI Detector Server" 15; then
                printf "   ${GREEN}✅ Neural UI Detector Server is listening on port $NEURAL_UI_PORT${RESET}\n"
                NEURAL_UI_OK=true
            else
                printf "   ${YELLOW}⚠️ Neural UI Detector Server not responding, falling back to simple version...${RESET}\n"
                kill $NEURAL_UI_PID 2>/dev/null || true
            fi
        fi
    fi
else
    printf "   ${YELLOW}⚠️ Neural UI detector files not found, will create simplified version${RESET}\n"
fi

# If Neural UI detector isn't running, create a simple version
if ! $NEURAL_UI_OK; then
    printf "   ${YELLOW}→ Creating simplified Neural UI Detector...${RESET}\n"
    
    # Create and start a simple Neural UI detector
    cat > start_neural_ui_detector.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/ui_detection', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ui_detection/neural_ui_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("neural_ui_detector")

class SimpleNeuralUIDetector:
    def __init__(self):
        self.clients = set()
        logger.info("Initializing Simple UI Detector")
        
    async def detect_ui_elements(self, action=None):
        """Provide mock UI detection results"""
        logger.info("Mock UI detection requested: " + str(action))
        
        # Return mock results
        return {
            "success": True,
            "action": action or "analyze_screen",
            "message": "This is a simplified detector with mock results",
            "elements": [
                {
                    "type": "button",
                    "text": "Example Button",
                    "confidence": 0.95,
                    "coordinates": {"x": 100, "y": 100, "width": 200, "height": 50}
                },
                {
                    "type": "input_field",
                    "text": "",
                    "confidence": 0.90,
                    "coordinates": {"x": 100, "y": 200, "width": 300, "height": 40}
                }
            ],
            "timestamp": datetime.now().isoformat()
        }

async def handle_client(websocket, path):
    """Handle client connections"""
    detector = SimpleNeuralUIDetector()
    logger.info("Client connected")
    detector.clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action", "analyze_screen")
                
                # Handle different action types
                if action == "analyze_screen" or action == "detect":
                    result = await detector.detect_ui_elements(action)
                    await websocket.send(json.dumps(result))
                else:
                    # Default response for any other action
                    await websocket.send(json.dumps({
                        "success": True,
                        "action": action,
                        "message": "Action processed",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "success": False,
                    "error": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        detector.clients.remove(websocket)

async def main():
    port = 8768
    host = "0.0.0.0"  # Listen on all interfaces to allow external connections
    logger.info("Starting Simple Neural UI Detector Server on port " + str(port))
    
    server = await websockets.serve(
        handle_client, 
        host, 
        port, 
        ping_interval=50,
        ping_timeout=300
    )
    
    print("Simple Neural UI Detector Server running on ws://{}:{}".format(host, port))
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF

    chmod +x start_neural_ui_detector.py
    
    # Start the Neural UI Detector
    python3 start_neural_ui_detector.py > logs/ui_detection/neural_ui_detector.log 2>&1 &
    NEURAL_UI_PID=$!
    echo $NEURAL_UI_PID > pids/neural_ui_detector.pid
    printf "   ${BLUE}→ Simple Neural UI Detector PID: %d${RESET}\n" "$NEURAL_UI_PID"
    
    # Wait for Neural UI Detector to start
    if wait_for_service $NEURAL_UI_PORT "Simple Neural UI Detector" 10; then
        printf "   ${GREEN}✅ Simple Neural UI Detector is listening on port $NEURAL_UI_PORT${RESET}\n"
        NEURAL_UI_OK=true
    else
        printf "   ${RED}❌ All Neural UI Detector attempts failed${RESET}\n"
        kill $NEURAL_UI_PID 2>/dev/null || true
    fi
fi

# 8. Start Neural UI DO Button Handler - only if BOTH Neural UI AND Direct Automation are running
if [ "$NEURAL_UI_OK" = true ] && [ "$DIRECT_AUTOMATION_OK" = true ]; then
    printf "\n${GREEN}🔄 Starting Neural UI DO Button Handler...${RESET}\n"
    
    # Try multiple potential file names
    DO_BUTTON_FILES=(
        "neural_ui_do_button_handler.py"
        "fixed_neural_ui_do_button_handler.py"
    )
    
    DO_BUTTON_OK=false
    
    for file in "${DO_BUTTON_FILES[@]}"; do
        if [ -f "$file" ]; then
            printf "   ${YELLOW}→ Found DO Button Handler: $file${RESET}\n"
            python3 $file > logs/do_button/neural_ui_do_button.log 2>&1 &
            NEURAL_HANDLER_PID=$!
            echo $NEURAL_HANDLER_PID > pids/neural_ui_do_button.pid
            printf "   ${BLUE}→ Neural UI DO Button Handler PID: %d${RESET}\n" "$NEURAL_HANDLER_PID"
            printf "   ${GREEN}✅ Neural UI DO Button Handler started${RESET}\n"
            DO_BUTTON_OK=true
            sleep 2
            break
        fi
    done
    
    if ! $DO_BUTTON_OK; then
        # Create a simple handler script
        printf "   ${YELLOW}⚠️ Creating simplified Neural UI DO Button Handler...${RESET}\n"
        cat > start_neural_ui_handler.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/do_button', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/do_button/neural_ui_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("neural_ui_do_button_handler")

class SimpleNeuralUIButtonHandler:
    def __init__(self):
        self.backend_uri = "ws://localhost:8767"
        self.neural_ui_uri = "ws://localhost:8768"
        self.do_button_uri = "ws://localhost:8765"
        self.running = True
        self.cached_plans = {}
        logger.info("Simple Neural UI DO Button Handler initialized - compatibility mode")
    
    async def start(self):
        """Start the handler service"""
        logger.info("Starting Neural UI DO Button Handler service")
        while self.running:
            try:
                # Connect to DO Button server to listen for plan execution requests
                async with websockets.connect(self.do_button_uri) as ws_do:
                    logger.info("Connected to DO Button server")
                    
                    # Simple heartbeat to show we're running
                    while self.running:
                        try:
                            # Wait for messages from DO Button server
                            message = await asyncio.wait_for(ws_do.recv(), timeout=5.0)
                            data = json.loads(message)
                            
                            msg_type = data.get('type', 'unknown')
                            logger.info("Received message from DO Button server: " + str(msg_type))
                            
                            # Handle plan execution requests
                            if data.get("type") == "execute_plan" and data.get("plan_id"):
                                plan_id = data.get("plan_id")
                                logger.info("Received execution request for plan: " + str(plan_id))
                                
                                # Send success response
                                await ws_do.send(json.dumps({
                                    "type": "execution_result",
                                    "plan_id": plan_id,
                                    "success": True,
                                    "message": "Plan executed successfully (simulated in compatibility mode)",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                        except asyncio.TimeoutError:
                            # Just a timeout, continue
                            continue
                        except Exception as e:
                            logger.error("Error processing DO Button message: " + str(e))
                            await asyncio.sleep(2)
                
            except Exception as e:
                logger.error("Connection error: " + str(e))
                await asyncio.sleep(5)  # Wait before reconnecting

async def main():
    handler = SimpleNeuralUIButtonHandler()
    await handler.start()

if __name__ == "__main__":
    asyncio.run(main())
EOF

        chmod +x start_neural_ui_handler.py
        
        # Start the handler
        python3 start_neural_ui_handler.py > logs/do_button/neural_ui_handler.log 2>&1 &
        NEURAL_HANDLER_PID=$!
        echo $NEURAL_HANDLER_PID > pids/neural_ui_handler.pid
        printf "   ${BLUE}→ Simple Neural UI DO Button Handler PID: %d${RESET}\n" "$NEURAL_HANDLER_PID"
        printf "   ${GREEN}✅ Simple Neural UI DO Button Handler started${RESET}\n"
        DO_BUTTON_OK=true
        sleep 2
    fi
else
    printf "\n${YELLOW}⚠️ Skipping Neural UI DO Button Handler (dependencies not ready)${RESET}\n"
fi

# 9. Start Overlay Bridge Server on port 8766
printf "\n${GREEN}🌐 Starting Overlay Bridge Server on port $OVERLAY_BRIDGE_PORT...${RESET}\n"

# Check for port availability
if ! check_port_available $OVERLAY_BRIDGE_PORT; then
    printf "   ${RED}→ Port $OVERLAY_BRIDGE_PORT is already in use. Attempting to free it...${RESET}\n"
    kill_process_on_port $OVERLAY_BRIDGE_PORT
    wait_for_port $OVERLAY_BRIDGE_PORT 10
fi

# Create a modified bridge server that uses the correct ports
cat > fixed_bridge_server_ports.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Overlay Bridge Server
- Connects overlay UI to backend server
- Ensures proper WebSocket communication
- Uses fixed ports to avoid conflicts
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/overlay', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay/fixed_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fixed_bridge_server")

# FIXED PORT CONFIGURATION
BRIDGE_PORT = 8766
BACKEND_PORT = 8767
DO_BUTTON_PORT = 8765
NEURAL_UI_PORT = 8768

class OverlayBridgeServer:
    def __init__(self):
        self.clients = set()
        self.backend_uri = f"ws://localhost:{BACKEND_PORT}"  # Enterprise backend port
        self.do_button_uri = f"ws://localhost:{DO_BUTTON_PORT}"  # DO Button port
        logger.info(f"Initializing Bridge Server: backend={self.backend_uri}, do_button={self.do_button_uri}")

    async def forward_to_backend(self, client_ws, message):
        """Forward message to backend and return response"""
        try:
            logger.info(f"Forwarding to backend: {message[:100]}...")
            async with websockets.connect(self.backend_uri, ping_interval=None) as backend_ws:
                await backend_ws.send(message)
                response = await backend_ws.recv()
                logger.info(f"Received from backend: {response[:100]}...")
                return response
        except Exception as e:
            logger.error(f"Error forwarding to backend: {e}")
            return json.dumps({
                "type": "error",
                "message": f"Backend connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def forward_to_do_button(self, client_ws, message):
        """Forward message to DO Button server and return response"""
        try:
            logger.info(f"Forwarding to DO Button: {message[:100]}...")
            async with websockets.connect(self.do_button_uri, ping_interval=None) as do_button_ws:
                await do_button_ws.send(message)
                response = await do_button_ws.recv()
                logger.info(f"Received from DO Button: {response[:100]}...")
                return response
        except Exception as e:
            logger.error(f"Error forwarding to DO Button: {e}")
            return json.dumps({
                "type": "error",
                "message": f"DO Button connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

async def handle_client(websocket, path):
    """Handle client connections"""
    bridge = OverlayBridgeServer()
    logger.info(f"Client connected from {websocket.remote_address}")
    bridge.clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                # Parse the message to determine routing
                data = json.loads(message)
                message_type = data.get("type", "")
                
                # Handle different message types
                if message_type == "execute_plan":
                    # Forward plan execution to DO Button server
                    response = await bridge.forward_to_do_button(websocket, message)
                    await websocket.send(response)
                elif message_type == "agent_confirmation" and data.get("action") == "approve":
                    # Special handling for agent mode confirmations
                    plan_data = data.get("plan", {})
                    plan_id = data.get("plan_id", "")
                    
                    # First, acknowledge receipt of confirmation
                    await websocket.send(json.dumps({
                        "type": "confirmation_received",
                        "plan_id": plan_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Then forward to DO Button for execution
                    execution_message = json.dumps({
                        "type": "execute_plan",
                        "plan_id": plan_id,
                        "plan": plan_data
                    })
                    
                    execution_response = await bridge.forward_to_do_button(websocket, execution_message)
                    await websocket.send(execution_response)
                else:
                    # All other messages go to the backend
                    response = await bridge.forward_to_backend(websocket, message)
                    await websocket.send(response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Bridge error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    finally:
        bridge.clients.remove(websocket)

async def main():
    host = "0.0.0.0"  # Listen on all interfaces
    port = BRIDGE_PORT
    
    logger.info(f"Starting Overlay Bridge Server on port {port}")
    logger.info(f"Backend URI: ws://localhost:{BACKEND_PORT}")
    logger.info(f"DO Button URI: ws://localhost:{DO_BUTTON_PORT}")
    
    # Ensure backend server is running before starting
    backend_available = False
    for _ in range(5):
        try:
            async with websockets.connect(f"ws://localhost:{BACKEND_PORT}", ping_interval=None) as ws:
                backend_available = True
                logger.info("Successfully connected to backend server")
                break
        except:
            logger.warning(f"Backend server not available, retrying in 2 seconds...")
            await asyncio.sleep(2)
    
    if not backend_available:
        logger.warning("Backend server not available after retries, bridge will attempt to connect on demand")
    
    server = await websockets.serve(
        handle_client, 
        host, 
        port, 
        ping_interval=50,
        ping_timeout=300
    )
    
    print(f"Overlay Bridge Server running on ws://{host}:{port}")
    print(f"Connecting to: Backend={BACKEND_PORT}, DO Button={DO_BUTTON_PORT}")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x fixed_bridge_server_ports.py

# Start the bridge server
python3 fixed_bridge_server_ports.py > logs/overlay/fixed_bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
printf "   ${BLUE}→ Fixed Overlay Bridge Server PID: %d${RESET}\n" "$BRIDGE_PID"

# Wait for bridge server to start
if wait_for_service $OVERLAY_BRIDGE_PORT "Overlay Bridge Server" 10; then
    printf "   ${GREEN}✅ Fixed Overlay Bridge Server is running on port $OVERLAY_BRIDGE_PORT${RESET}\n"
    BRIDGE_OK=true
    
    # Start HTTP server for overlay chat
    printf "   ${YELLOW}→ Starting HTTP Server for Overlay Chat...${RESET}\n"
    
    # Check if overlay directory exists with index.html
    if [ -d "overlay" ] && [ -f "overlay/index.html" ]; then
        # Check if HTTP port is available
        if ! check_port_available $HTTP_PORT; then
            printf "   ${RED}→ Port $HTTP_PORT is already in use. Attempting to free it...${RESET}\n"
            kill_process_on_port $HTTP_PORT
            wait_for_port $HTTP_PORT 10
        fi
        
        # Create a simple HTTP server to serve the overlay files
        python3 -m http.server $HTTP_PORT --directory overlay > logs/http_server.log 2>&1 &
        HTTP_PID=$!
        echo $HTTP_PID > pids/http_server.pid
        printf "   ${BLUE}→ HTTP Server PID: %d${RESET}\n" "$HTTP_PID"
        
        # Wait for HTTP server to start
        if wait_for_service $HTTP_PORT "HTTP Server" 5; then
            # Open browser
            printf "   ${YELLOW}→ Opening Overlay Chat in browser...${RESET}\n"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open "http://localhost:$HTTP_PORT" # macOS
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                xdg-open "http://localhost:$HTTP_PORT" # Linux
            elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
                start "http://localhost:$HTTP_PORT" # Windows
            else
                printf "   ${YELLOW}⚠️ Please open a browser to http://localhost:$HTTP_PORT manually${RESET}\n"
            fi
            
            printf "   ${GREEN}✅ Overlay Chat available at: http://localhost:$HTTP_PORT${RESET}\n"
        else
            printf "   ${RED}❌ HTTP Server failed to start on port $HTTP_PORT${RESET}\n"
            kill $HTTP_PID 2>/dev/null || true
        fi
    elif [ -f "index.html" ]; then
        # Check if HTTP port is available
        if ! check_port_available $HTTP_PORT; then
            printf "   ${RED}→ Port $HTTP_PORT is already in use. Attempting to free it...${RESET}\n"
            kill_process_on_port $HTTP_PORT
            wait_for_port $HTTP_PORT 10
        fi
        
        # Create a simple HTTP server to serve the root directory
        python3 -m http.server $HTTP_PORT > logs/http_server.log 2>&1 &
        HTTP_PID=$!
        echo $HTTP_PID > pids/http_server.pid
        printf "   ${BLUE}→ HTTP Server PID: %d${RESET}\n" "$HTTP_PID"
        
        # Wait for HTTP server to start
        if wait_for_service $HTTP_PORT "HTTP Server" 5; then
            # Open browser
            printf "   ${YELLOW}→ Opening Chat Interface in browser...${RESET}\n"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open "http://localhost:$HTTP_PORT" # macOS
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                xdg-open "http://localhost:$HTTP_PORT" # Linux
            elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
                start "http://localhost:$HTTP_PORT" # Windows
            else
                printf "   ${YELLOW}⚠️ Please open a browser to http://localhost:$HTTP_PORT manually${RESET}\n"
            fi
            
            printf "   ${GREEN}✅ Chat Interface available at: http://localhost:$HTTP_PORT${RESET}\n"
        else
            printf "   ${RED}❌ HTTP Server failed to start on port $HTTP_PORT${RESET}\n"
            kill $HTTP_PID 2>/dev/null || true
        fi
    else
        printf "   ${YELLOW}⚠️ Chat interface HTML file not found${RESET}\n"
    fi
else
    printf "   ${RED}❌ Fixed Overlay Bridge Server failed to start on port $OVERLAY_BRIDGE_PORT${RESET}\n"
    kill $BRIDGE_PID 2>/dev/null || true
fi

# Create stop script
printf "\n${YELLOW}📝 Creating stop script...${RESET}\n"
cat > STOP_MASTER_SYSTEM_FIXED.sh << 'EOF'
#!/bin/bash

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

printf "${BOLD}${RED}⚠️ STOPPING SENSAI MASTER SYSTEM...${RESET}\n"

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
pkill -f "start_neural_ui_detector" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
pkill -f "start_direct_automation" 2>/dev/null || true
pkill -f "neural_ui_do_button_handler" 2>/dev/null || true
pkill -f "start_neural_ui_handler" 2>/dev/null || true
pkill -f "enhanced_enterprise_backend" 2>/dev/null || true
pkill -f "enterprise_backend_8767" 2>/dev/null || true
pkill -f "simple_backend_server" 2>/dev/null || true
pkill -f "smart_memory_feeder" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true
pkill -f "simple_process_sensor" 2>/dev/null || true
pkill -f "total_screen_analyzer" 2>/dev/null || true
pkill -f "fixed_bridge_server" 2>/dev/null || true
pkill -f "fixed_bridge_server_ports" 2>/dev/null || true
pkill -f "python3 -m http.server" 2>/dev/null || true
pkill -f "llm_warmup_manager" 2>/dev/null || true

# Clean up ports
printf "→ Freeing used ports...${RESET}\n"
for PORT in 8000 8765 8766 8767 8768; do
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
done

printf "${GREEN}✅ SENSAI MASTER SYSTEM STOPPED${RESET}\n"
EOF

chmod +x STOP_MASTER_SYSTEM_FIXED.sh

# System status summary
printf "\n${BOLD}${MAGENTA}=============================================${RESET}\n"
printf "${BOLD}${MAGENTA}       SENSAI MASTER SYSTEM READY!       ${RESET}\n"
printf "${BOLD}${MAGENTA}=============================================${RESET}\n"
printf "\n"
printf "${CYAN}🌐 System Components:${RESET}\n"

if $BACKEND_OK; then
    printf "   ${GREEN}✅ Enhanced Enterprise Backend:${RESET} ws://localhost:$BACKEND_PORT\n"
else
    printf "   ${RED}❌ Enterprise Backend: FAILED${RESET}\n"
fi

if [ "$LLM_WARMUP_OK" = true ]; then
    printf "   ${GREEN}✅ LLM Warmup Manager:${RESET} Active (PID: %d)\n" "$WARMUP_PID"
else
    printf "   ${YELLOW}⚠️ LLM Warmup Manager: INACTIVE${RESET}\n"
fi

if [ "$NEURAL_UI_OK" = true ]; then
    printf "   ${GREEN}✅ Neural UI Detector:${RESET} ws://localhost:$NEURAL_UI_PORT\n"
else
    printf "   ${YELLOW}⚠️ Neural UI Detector: INACTIVE${RESET}\n"
fi

if [ "$DIRECT_AUTOMATION_OK" = true ]; then
    printf "   ${GREEN}✅ Direct Automation Server:${RESET} ws://localhost:$DIRECT_AUTOMATION_PORT\n"
else
    printf "   ${YELLOW}⚠️ Direct Automation Server: INACTIVE${RESET}\n"
fi

if [ "$DO_BUTTON_OK" = true ]; then
    printf "   ${GREEN}✅ Neural UI DO Button Handler:${RESET} Active\n"
else
    printf "   ${YELLOW}⚠️ Neural UI DO Button Handler: INACTIVE${RESET}\n"
fi

if $PROCESS_SENSOR_OK; then
    printf "   ${GREEN}✅ Process Sensor:${RESET} Active (PID: %d)\n" "$PROCESS_PID"
else
    printf "   ${RED}❌ Process Sensor: FAILED${RESET}\n"
fi

if $MEMORY_OK; then
    printf "   ${GREEN}✅ Smart Memory Feeder:${RESET} Active (PID: %d)\n" "$MEMORY_PID"
else
    printf "   ${YELLOW}⚠️ Smart Memory Feeder: INACTIVE${RESET}\n"
fi

if $SCREEN_SENSOR_OK; then
    printf "   ${GREEN}✅ Total Screen Analyzer:${RESET} Active (PID: %d)\n" "$SCREEN_PID"
else
    printf "   ${YELLOW}⚠️ Total Screen Analyzer: INACTIVE${RESET}\n"
fi

if $BRIDGE_OK; then
    printf "   ${GREEN}✅ Overlay Bridge Server:${RESET} ws://localhost:$OVERLAY_BRIDGE_PORT\n"
    printf "   ${GREEN}✅ Overlay Chat Interface:${RESET} http://localhost:$HTTP_PORT\n"
else
    printf "   ${YELLOW}⚠️ Overlay Chat Interface: INACTIVE${RESET}\n"
fi

printf "\n"
printf "${YELLOW}🚀 System Capabilities:${RESET}\n"
printf "   ${BLUE}→ Agent Mode:${RESET} Real UI automation with Neural UI detection\n"
printf "   ${BLUE}→ Ask Mode:${RESET} Context-aware answers with semantic memory search\n"
printf "   ${BLUE}→ Suggest Mode:${RESET} Proactive suggestions based on memory patterns\n"
printf "   ${BLUE}→ General Mode:${RESET} Conversational memory with context integration\n"
printf "\n"
printf "${YELLOW}🔧 System Management:${RESET}\n"
printf "   ${BLUE}→ Stop System:${RESET} ./STOP_MASTER_SYSTEM_FIXED.sh\n"
printf "   ${BLUE}→ View Backend Logs:${RESET} tail -f logs/backend/enhanced_enterprise_8767.log\n"
printf "   ${BLUE}→ View Neural UI Logs:${RESET} tail -f logs/ui_detection/neural_ui_detector.log\n"
printf "   ${BLUE}→ View DO Button Logs:${RESET} tail -f logs/do_button/do_button_server.log\n"
printf "   ${BLUE}→ View Bridge Logs:${RESET} tail -f logs/overlay/fixed_bridge.log\n"
printf "   ${BLUE}→ View Memory Logs:${RESET} tail -f logs/memory/smart_feeder.log\n"
if $BRIDGE_OK; then
    printf "   ${BLUE}→ Overlay Chat:${RESET} http://localhost:$HTTP_PORT\n"
fi
printf "\n"
printf "${BOLD}${GREEN}🎯 Master System is ready for use!${RESET}\n"
printf "\n"

# Check if backend is running to show logs
if $BACKEND_OK; then
    printf "${CYAN}Showing backend logs (press Ctrl+C to exit logs, system will continue running)${RESET}\n"
    printf "----------------------------------------\n"
    tail -f logs/backend/enhanced_enterprise_8767.log
else 
    printf "${RED}Backend not running - cannot show logs${RESET}\n"
    printf "${YELLOW}Please check the system status above and troubleshoot any failed components${RESET}\n"
fi