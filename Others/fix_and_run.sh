#!/bin/bash
# Quick fix script to stop all running processes and start a correctly configured system

# Color codes for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
echo_color() {
  color=$1
  message=$2
  case $color in
    "green") echo -e "${GREEN}$message${NC}" ;;
    "yellow") echo -e "${YELLOW}$message${NC}" ;;
    "blue") echo -e "${BLUE}$message${NC}" ;;
    "red") echo -e "${RED}$message${NC}" ;;
    *) echo "$message" ;;
  esac
}

# Create necessary directories
mkdir -p logs/memory
mkdir -p logs/sensors/screen_sensor
mkdir -p logs/llm
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p memory

# Step 1: Kill all existing processes
echo_color "yellow" "Stopping all running processes..."
pkill -f "python3.*fixed_bridge_server.py" 2>/dev/null || true
pkill -f "python3.*enhanced_fixed_screen_sensor.py" 2>/dev/null || true
pkill -f "python3.*self_contained_llm_ws.py" 2>/dev/null || true
pkill -f "python3.*memory_system.py" 2>/dev/null || true
sleep 2

# Step 2: Fix screen sensor port issue by editing the file directly
echo_color "blue" "Fixing screen sensor port configuration..."
cat > sensors/fixed_screen_sensor.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Screen Sensor

This module captures screen information and sends it to the bridge server.
It properly updates the last_context.json file for LLM integration.
"""
import os
import json
import time
import asyncio
import logging
import websockets
import tempfile
import hashlib
import base64
import traceback
from datetime import datetime
from PIL import ImageGrab

# Configure logging
os.makedirs('logs/sensors/screen_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('screen_sensor')

class ScreenSensor:
    """Captures screen information and sends to bridge server"""
    
    def __init__(self, bridge_uri="ws://localhost:8767", capture_interval=5):
        self.bridge_uri = bridge_uri
        self.capture_interval = capture_interval
        self.running = True
        self.cache_dir = "cache/screen_sensor"
        self.last_screen_hash = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Screen sensor initialized with interval {capture_interval}s")
    
    def _capture_screen(self):
        """Capture screen and extract information"""
        try:
            # Take screenshot
            screenshot = ImageGrab.grab()
            
            # Save screenshot to temporary file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"screen_{int(time.time())}.png")
            screenshot.save(temp_file)
            
            # Get basic image info
            width, height = screenshot.size
            
            # Calculate image hash to detect changes
            img_hash = hashlib.md5(screenshot.tobytes()).hexdigest()
            
            # Prepare screen data
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "resolution": f"{width}x{height}",
                "image_hash": img_hash,
                "temp_file": temp_file,
                "active_window": "Darwin - Python 3.13.3",  # Simplified for demo
                "active_app": "Darwin"
            }
            
            # Check if screen has changed
            is_changed = self.last_screen_hash != img_hash
            screen_data["is_changed"] = is_changed
            
            if is_changed:
                self.last_screen_hash = img_hash
                logger.info(f"Captured screen with hash: {img_hash[:8]}... (changed)")
            else:
                logger.debug(f"Captured screen with hash: {img_hash[:8]}... (no change)")
            
            # Cache last screen data
            self._cache_screen_data(screen_data)
            
            # Update memory context directly
            self._update_last_context(screen_data)
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _cache_screen_data(self, screen_data):
        """Cache screen data to file"""
        try:
            # Create simplified version without the large base64 image
            cache_data = {
                "timestamp": screen_data["timestamp"],
                "resolution": screen_data["resolution"],
                "image_hash": screen_data["image_hash"],
                "active_window": screen_data["active_window"],
                "active_app": screen_data["active_app"],
                "is_changed": screen_data["is_changed"]
            }
            
            # Save to cache file
            cache_file = os.path.join(self.cache_dir, "last_screen.json")
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached screen data to {cache_file}")
            
        except Exception as e:
            logger.error(f"Error caching screen data: {e}")
    
    def _update_last_context(self, screen_data):
        """Update the last_context.json file with screen data for LLM integration"""
        try:
            # Create memory directory if it doesn't exist
            memory_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory')
            os.makedirs(memory_dir, exist_ok=True)
            
            # File path for last_context.json
            context_file = os.path.join(memory_dir, 'last_context.json')
            
            # Load existing context if available
            if os.path.exists(context_file):
                try:
                    with open(context_file, 'r') as f:
                        context = json.load(f)
                except json.JSONDecodeError:
                    context = {}
            else:
                context = {}
            
            # Update context with screen data
            context.update({
                "timestamp": int(time.time()),
                "active_window": screen_data.get("active_window", ""),
                "active_app": screen_data.get("active_app", ""),
                "screen_text": f"Screenshot captured at {screen_data.get('timestamp')} showing {screen_data.get('active_window', '')}",
                "visual_context": f"Screen showing {screen_data.get('active_app', '')} application with resolution {screen_data.get('resolution', '')}"
            })
            
            # Make sure active_apps is a list
            if "active_apps" not in context:
                context["active_apps"] = []
            
            # Add current app to active_apps if not already there
            active_app = screen_data.get("active_app")
            if active_app and active_app not in context["active_apps"]:
                context["active_apps"].insert(0, active_app)
                # Keep only the last 5 apps
                context["active_apps"] = context["active_apps"][:5]
            
            # Make sure window_history is a list
            if "window_history" not in context:
                context["window_history"] = []
            
            # Add current window to history if not already the most recent
            active_window = screen_data.get("active_window")
            if active_window:
                if not context["window_history"] or context["window_history"][0] != active_window:
                    context["window_history"].insert(0, active_window)
                    # Keep only the last 5 windows
                    context["window_history"] = context["window_history"][:5]
            
            # Write updated context to file
            with open(context_file, 'w') as f:
                json.dump(context, f, indent=2)
                
            logger.info(f"Updated last_context.json with active app: {active_app}")
        except Exception as e:
            logger.error(f"Error updating last_context.json: {e}")
    
    async def connect_to_bridge(self):
        """Connect to bridge server and send screen data"""
        while self.running:
            try:
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Identify as screen sensor
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "sensor",
                        "sensor_type": "screen",
                        "version": "1.0.0"
                    }))
                    
                    # Main loop for sending screen updates
                    while self.running:
                        try:
                            # Capture screen
                            screen_data = self._capture_screen()
                            if screen_data:
                                # Send to bridge server
                                await websocket.send(json.dumps({
                                    "type": "sensor_data",
                                    "sensor_type": "screen",
                                    "data": screen_data
                                }))
                                
                                logger.info(f"Sent screen data to bridge server")
                            
                            # Wait for next capture
                            await asyncio.sleep(self.capture_interval)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Connection to bridge server closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in main loop: {e}")
                            await asyncio.sleep(5)
                            
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the screen sensor"""
        logger.info("Starting screen sensor")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/screen_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to bridge and start sending data
        await self.connect_to_bridge()

# Run the screen sensor
async def run_screen_sensor():
    sensor = ScreenSensor()
    await sensor.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_screen_sensor())
    except KeyboardInterrupt:
        logger.info("Screen sensor stopped by user")
    except Exception as e:
        logger.error(f"Error running screen sensor: {e}")
        logger.error(traceback.format_exc())
EOF
chmod +x sensors/fixed_screen_sensor.py

# Step 3: Create minimal memory logger if it doesn't exist
echo_color "blue" "Creating memory logger module..."
cat > memory/memory_logger.py << 'EOF'
"""
Memory Logger Module

Provides logging functionality for the memory system.
"""
import logging
import os
import time
from datetime import datetime

class MemoryLogger:
    """Logger for memory-related operations"""
    
    def __init__(self, log_dir="logs/memory", log_level=logging.INFO):
        """Initialize the memory logger."""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("memory_system")
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        if self.logger.handlers:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(os.path.join(log_dir, "memory_system.log"))
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_format)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message."""
        self.logger.critical(message)
    
    def log_memory_update(self, memory_type, content_summary=None):
        """Log a memory update event."""
        timestamp = datetime.now().isoformat()
        if content_summary:
            self.info(f"Memory update: {memory_type} at {timestamp} - {content_summary}")
        else:
            self.info(f"Memory update: {memory_type} at {timestamp}")
    
    def log_memory_access(self, memory_type, query=None):
        """Log a memory access event."""
        if query:
            self.debug(f"Memory access: {memory_type} - query: {query}")
        else:
            self.debug(f"Memory access: {memory_type}")
    
    def log_context_update(self, context_type, content_summary=None):
        """Log a context update event."""
        if content_summary:
            self.info(f"Context update: {context_type} - {content_summary}")
        else:
            self.info(f"Context update: {context_type}")
    
    def log_error(self, operation, error_message):
        """Log an error during memory operations."""
        self.error(f"Error during {operation}: {error_message}")

# Default instance for import
default_logger = MemoryLogger()
EOF

# Step 4: Create minimal diagnostic logger if it doesn't exist
echo_color "blue" "Creating memory diagnostic logger module..."
cat > memory/memory_diagnostic_logger.py << 'EOF'
"""
Memory Diagnostic Logger Module

Provides simple diagnostic logging for memory operations.
"""
import logging
import os
import json
from datetime import datetime

class MemoryDiagnosticLogger:
    """Simple diagnostic logger for memory operations"""
    
    def __init__(self):
        self.logger = logging.getLogger("memory_diagnostics")
        
        # Set up logger only if not already configured
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # Ensure log directory exists
            os.makedirs("logs/memory", exist_ok=True)
            
            # Set up file handler
            handler = logging.FileHandler("logs/memory/diagnostics.log")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
    
    def log_operation(self, operation_type, details=None):
        """Log a memory operation"""
        if details:
            self.logger.info(f"Memory operation: {operation_type} - {details}")
        else:
            self.logger.info(f"Memory operation: {operation_type}")
    
    def log_error(self, error_type, message):
        """Log a memory error"""
        self.logger.error(f"Memory error: {error_type} - {message}")
    
    def log_stats(self, stats):
        """Log memory stats"""
        self.logger.info(f"Memory stats: {json.dumps(stats)}")

# Default instance
default_diagnostic_logger = MemoryDiagnosticLogger()
EOF

# Step 5: Create a Simplified LLM websocket server
echo_color "blue" "Creating minimal LLM service with context support..."
cat > simple_llm_ws.py << 'EOF'
#!/usr/bin/env python3
"""
Simple LLM WebSocket Server

Provides a WebSocket server for LLM integration with context awareness.
"""
import os
import json
import asyncio
import logging
import websockets
import time
import re
import traceback
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/simple_llm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_llm')

class SimpleLLMService:
    """Simple LLM service with WebSocket interface"""
    
    def __init__(self, host="localhost", port=8770):
        self.host = host
        self.port = port
        self.running = True
        logger.info(f"Simple LLM service initialized on {host}:{port}")
    
    def _load_context(self):
        """Load context from memory system"""
        try:
            # Path to last_context.json
            context_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory', 'last_context.json')
            
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    context = json.load(f)
                logger.info(f"Loaded context from {context_file}")
                return context
            else:
                logger.warning(f"Context file not found: {context_file}")
                return None
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return None
    
    def _generate_response(self, query, context=None):
        """Generate response using context"""
        try:
            # Load context if not provided
            if not context:
                context = self._load_context()
            
            # If no context available, provide a generic response
            if not context:
                return {
                    "response": "I don't have any context information available at the moment.",
                    "context_used": False
                }
            
            # Generate response based on query type and context
            if re.search(r'what\s+(?:am\s+I|are\s+you)\s+seeing', query, re.IGNORECASE):
                # Response for "What am I seeing?" type queries
                response = f"You are currently looking at {context.get('active_window', 'an unknown window')}. "
                
                if context.get('screen_text'):
                    response += f"The screen contains: {context.get('screen_text')}"
                
                return {
                    "response": response,
                    "context_used": True
                }
                
            elif re.search(r'what\s+(?:app|application)(?:\s+am\s+I|\s+are\s+you)?\s+using', query, re.IGNORECASE):
                # Response for application queries
                active_app = context.get('active_app', 'an unknown application')
                response = f"You are currently using {active_app}."
                
                if context.get('active_apps') and len(context.get('active_apps')) > 1:
                    other_apps = context.get('active_apps')[1:3]  # Get next 2 apps
                    response += f" Other recent applications include: {', '.join(other_apps)}."
                
                return {
                    "response": response,
                    "context_used": True
                }
                
            elif re.search(r'(?:summarize|summary|what\s+is|tell\s+me\s+about)\s+(?:my\s+)?context', query, re.IGNORECASE):
                # Response for context summary queries
                active_window = context.get('active_window', 'Unknown window')
                active_app = context.get('active_app', 'Unknown application')
                window_history = context.get('window_history', [])
                
                response = f"You are currently using {active_app} with the window '{active_window}'. "
                
                if window_history and len(window_history) > 1:
                    response += f"Recently visited windows include: {', '.join(window_history[1:3])}. "
                
                if context.get('screen_text'):
                    response += f"The screen content shows: {context.get('screen_text')}"
                
                return {
                    "response": response,
                    "context_used": True
                }
                
            else:
                # Generic response with context inclusion
                response = f"I'm not sure how to answer that specific question, but I can tell you that you're currently using {context.get('active_app', 'an application')} with the window '{context.get('active_window', 'unknown')}'. "
                
                if context.get('screen_text'):
                    response += f"Your screen shows: {context.get('screen_text')}"
                
                return {
                    "response": response,
                    "context_used": True
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I encountered an error while processing your request.",
                "context_used": False,
                "error": str(e)
            }
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                try:
                    # Parse message
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    # Handle different message types
                    if message_type == 'llm_request':
                        # Extract query and context
                        query = data.get('query', '')
                        context = data.get('context')
                        include_context = data.get('include_context', True)
                        request_id = data.get('request_id', str(int(time.time())))
                        
                        logger.info(f"Received LLM request: '{query}'")
                        
                        # Generate response
                        if include_context:
                            response_data = self._generate_response(query, context)
                        else:
                            response_data = {
                                "response": "This is a response without context integration.",
                                "context_used": False
                            }
                        
                        # Send response
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "request_id": request_id,
                            "query": query,
                            "response": response_data.get("response"),
                            "context_used": response_data.get("context_used", False),
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        logger.info(f"Sent response to client {client_id}")
                        
                    elif message_type == 'ping':
                        # Respond to ping
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    else:
                        # Handle unknown message type
                        logger.warning(f"Unknown message type: {message_type}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}",
                            "timestamp": datetime.now().isoformat()
                        }))
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    logger.error(traceback.format_exc())
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Internal server error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
            logger.error(traceback.format_exc())
    
    async def run(self):
        """Run the LLM service"""
        logger.info(f"Starting LLM service on {self.host}:{self.port}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open("pids/llm_service.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"LLM service is running at ws://{self.host}:{self.port}")
            
            # Keep the server running
            while self.running:
                await asyncio.sleep(1)

# Run the LLM service
if __name__ == "__main__":
    try:
        service = SimpleLLMService()
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("LLM service stopped by user")
    except Exception as e:
        logger.error(f"Error running LLM service: {e}")
        logger.error(traceback.format_exc())
EOF
chmod +x simple_llm_ws.py

# Step 6: Create minimal memory system
echo_color "blue" "Creating minimal memory system with context support..."
cat > memory/minimal_memory_system.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal Memory System

Provides a basic memory system that maintains context for LLM integration.
"""
import os
import json
import logging
import time
import asyncio
import websockets
from datetime import datetime
import traceback

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_system')

class MinimalMemorySystem:
    """Minimal memory system that maintains context"""
    
    def __init__(self, memory_dir="memory", memory_file="memory_state.json", host="localhost", port=8769):
        self.memory_dir = memory_dir
        self.memory_file = os.path.join(memory_dir, memory_file)
        self.host = host
        self.port = port
        self.running = True
        
        # Create memory directory if it doesn't exist
        os.makedirs(memory_dir, exist_ok=True)
        
        # Initialize memory state
        self.memory_state = self._load_memory_state()
        
        logger.info("Minimal memory system initialized")
    
    def _load_memory_state(self):
        """Load memory state from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize empty memory state
                return {
                    "short_term": [],
                    "context": {},
                    "last_update": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            return {
                "short_term": [],
                "context": {},
                "last_update": datetime.now().isoformat()
            }
    
    def _save_memory_state(self):
        """Save memory state to file"""
        try:
            # Update last_update timestamp
            self.memory_state["last_update"] = datetime.now().isoformat()
            
            # Save memory state
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_state, f, indent=2)
            
            # Also update last_context.json for LLM integration
            self._update_context()
            
            logger.debug("Memory state saved")
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
    
    def _update_context(self):
        """Update last_context.json with current context"""
        try:
            # Get current context
            context = self.memory_state.get("context", {})
            
            # Create context file path
            context_file = os.path.join(self.memory_dir, "last_context.json")
            
            # Save context
            with open(context_file, 'w') as f:
                json.dump(context, f, indent=2)
            
            logger.info("Context updated in last_context.json")
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    def _process_sensor_data(self, data, sensor_type):
        """Process sensor data and update memory and context"""
        try:
            if sensor_type == "screen":
                # Extract key data from screen sensor
                active_window = data.get("active_window", "Unknown window")
                active_app = data.get("active_app", "Unknown application")
                timestamp = data.get("timestamp", datetime.now().isoformat())
                resolution = data.get("resolution", "Unknown")
                
                # Create screen text with timestamp
                screen_text = f"Screenshot captured at {timestamp} showing {active_window}"
                
                # Create visual context description
                visual_context = f"Screen showing {active_app} application with resolution {resolution}"
                
                # Update context with screen data
                context = self.memory_state.get("context", {})
                
                context.update({
                    "timestamp": int(time.time()),
                    "active_window": active_window,
                    "active_app": active_app,
                    "screen_text": screen_text,
                    "visual_context": visual_context
                })
                
                # Update active_apps list
                if "active_apps" not in context:
                    context["active_apps"] = []
                
                if active_app and active_app not in context["active_apps"]:
                    context["active_apps"].insert(0, active_app)
                    # Keep only the last 5 apps
                    context["active_apps"] = context["active_apps"][:5]
                
                # Update window_history list
                if "window_history" not in context:
                    context["window_history"] = []
                
                if active_window and (not context["window_history"] or context["window_history"][0] != active_window):
                    context["window_history"].insert(0, active_window)
                    # Keep only the last 5 windows
                    context["window_history"] = context["window_history"][:5]
                
                # Update memory state with new context
                self.memory_state["context"] = context
                
                # Save memory state and update context
                self._save_memory_state()
                
                logger.info(f"Processed screen data: {active_window}")
                
            elif sensor_type == "process":
                # Extract key data from process sensor
                processes = data.get("processes", [])
                active_processes = data.get("active_processes", [])
                
                # Update context with process data
                context = self.memory_state.get("context", {})
                
                # Add active processes to context
                context["active_processes"] = active_processes
                
                # Add top 5 processes by memory usage to context
                top_processes = sorted(processes, key=lambda p: p.get("memory", 0), reverse=True)[:5]
                context["top_processes"] = [p.get("name", "Unknown") for p in top_processes]
                
                # Update memory state with new context
                self.memory_state["context"] = context
                
                # Save memory state and update context
                self._save_memory_state()
                
                logger.info(f"Processed process data: {len(processes)} processes")
                
            elif sensor_type == "file":
                # Extract key data from file sensor
                files = data.get("files", [])
                current_file = data.get("current_file", "")
                
                # Update context with file data
                context = self.memory_state.get("context", {})
                
                # Add current file to context
                if current_file:
                    context["current_file"] = current_file
                
                # Add recent files to context
                if files:
                    context["recent_files"] = files[:5]
                
                # Update memory state with new context
                self.memory_state["context"] = context
                
                # Save memory state and update context
                self._save_memory_state()
                
                logger.info(f"Processed file data: {current_file}")
                
            else:
                logger.warning(f"Unknown sensor type: {sensor_type}")
                
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            logger.error(traceback.format_exc())
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                try:
                    # Parse message
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    # Handle different message types
                    if message_type == 'sensor_data':
                        # Extract sensor type and data
                        sensor_type = data.get('sensor_type', '')
                        sensor_data = data.get('data', {})
                        
                        logger.info(f"Received sensor data from {sensor_type}")
                        
                        # Process sensor data
                        self._process_sensor_data(sensor_data, sensor_type)
                        
                        # Send acknowledgement
                        await websocket.send(json.dumps({
                            "type": "ack",
                            "message": f"Processed {sensor_type} data",
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    elif message_type == 'get_context':
                        # Send current context
                        await websocket.send(json.dumps({
                            "type": "context",
                            "data": self.memory_state.get("context", {}),
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    elif message_type == 'ping':
                        # Respond to ping
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    else:
                        # Handle unknown message type
                        logger.warning(f"Unknown message type: {message_type}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}",
                            "timestamp": datetime.now().isoformat()
                        }))
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    logger.error(traceback.format_exc())
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Internal server error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
            logger.error(traceback.format_exc())
    
    async def run(self):
        """Run the memory system"""
        logger.info(f"Starting memory system on {self.host}:{self.port}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open("pids/memory_system.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"Memory system is running at ws://{self.host}:{self.port}")
            
            # Keep the server running
            while self.running:
                await asyncio.sleep(1)

# Run the memory system
if __name__ == "__main__":
    try:
        memory_system = MinimalMemorySystem()
        asyncio.run(memory_system.run())
    except KeyboardInterrupt:
        logger.info("Memory system stopped by user")
    except Exception as e:
        logger.error(f"Error running memory system: {e}")
        logger.error(traceback.format_exc())
EOF
chmod +x memory/minimal_memory_system.py

# Step 7: Create test script for LLM requests
echo_color "blue" "Creating test script for LLM requests..."
cat > test_llm_request.py << 'EOF'
#!/usr/bin/env python3
"""
Test LLM Request

Test the LLM service with a user query and show the response.
"""
import asyncio
import websockets
import json
import sys
import os
import time

async def test_llm_request(query):
    """Send a query to the LLM service and get the response"""
    uri = "ws://localhost:8770"
    
    print(f"Connecting to LLM service at {uri}...")
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # First check context
        context_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory', 'last_context.json')
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context = json.load(f)
                print("\nCURRENT CONTEXT:")
                print(json.dumps(context, indent=2))
        
        # Send request
        request = {
            "type": "llm_request",
            "query": query,
            "include_context": True,
            "request_id": f"test_{int(time.time())}"
        }
        
        print(f"\nSending query: '{query}'")
        await websocket.send(json.dumps(request))
        
        # Wait for response
        print("Waiting for response...")
        response = await websocket.recv()
        response_data = json.loads(response)
        
        # Display response
        print("\n" + "=" * 60)
        print(f"QUERY: {query}")
        print("=" * 60)
        
        if "error" in response_data:
            print(f"ERROR: {response_data['error']}")
        else:
            print(f"CONTEXT USED: {'Yes' if response_data.get('context_used', False) else 'No'}")
            print(f"\nRESPONSE:")
            print(response_data.get("response", "No response"))
        
        print("=" * 60)

if __name__ == "__main__":
    # Get query from command line argument or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "What am I seeing?"
    
    # Run test
    asyncio.run(test_llm_request(query))
EOF
chmod +x test_llm_request.py

# Step 8: Start the system
echo_color "blue" "Starting the system..."

# Start bridge server
echo_color "blue" "Starting bridge server..."
python3 fixed_bridge_server.py > logs/bridge_server.log 2>&1 &
echo $! > pids/bridge_server.pid
sleep 2

# Start memory system
echo_color "blue" "Starting memory system..."
python3 memory/minimal_memory_system.py > logs/memory/memory_system.log 2>&1 &
echo $! > pids/memory_system.pid
sleep 2

# Start screen sensor
echo_color "blue" "Starting screen sensor..."
python3 sensors/fixed_screen_sensor.py > logs/sensors/screen_sensor/screen_sensor.log 2>&1 &
echo $! > pids/screen_sensor.pid
sleep 2

# Start LLM service
echo_color "blue" "Starting LLM service..."
python3 simple_llm_ws.py > logs/llm/simple_llm.log 2>&1 &
echo $! > pids/llm_service.pid
sleep 2

# Check if all services are running
echo_color "green" "All services started!"
echo
echo_color "green" "=============================================="
echo_color "green" "Context integration system is now running!"
echo_color "green" "=============================================="
echo
echo_color "blue" "You can test the system with:"
echo "  python3 test_llm_request.py \"What am I seeing?\""
echo "  python3 test_llm_request.py \"What application am I using?\""
echo "  python3 test_llm_request.py \"Summarize my current context\""
echo
echo_color "yellow" "Monitor the system with:"
echo "  tail -f logs/bridge_server.log"
echo "  tail -f logs/memory/memory_system.log"
echo "  tail -f logs/sensors/screen_sensor/screen_sensor.log"
echo "  tail -f logs/llm/simple_llm.log"
echo
echo_color "yellow" "To stop the system:"
echo "  ./fix_and_run.sh stop"
echo

# Check for stop command
if [ "$1" == "stop" ]; then
    echo_color "yellow" "Stopping all services..."
    pkill -f "python3.*fixed_bridge_server.py" 2>/dev/null || true
    pkill -f "python3.*fixed_screen_sensor.py" 2>/dev/null || true
    pkill -f "python3.*simple_llm_ws.py" 2>/dev/null || true
    pkill -f "python3.*minimal_memory_system.py" 2>/dev/null || true
    
    # Remove PID files
    rm -f pids/*.pid
    
    echo_color "green" "All services stopped."
    exit 0
fi