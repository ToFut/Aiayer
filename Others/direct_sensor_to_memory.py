#!/usr/bin/env python3
"""
Direct Sensor to Memory Integration

This script handles direct integration between sensors and memory by:
1. Monitoring sensor cache files
2. Directly updating memory state and context
3. Bypassing the need for explicit WebSocket connections
"""
import json
import os
import time
import logging
import traceback
import asyncio
import sys
from datetime import datetime
import shutil

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/direct_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('direct_sensor_memory')

# Configuration
MEMORY_STATE_FILE = "memory/memory_state.json"
CONTEXT_FILE = "memory/last_context.json"
PROCESS_CACHE = "cache/process_sensor/process_cache.json"
SCREEN_CACHE = "cache/screen_sensor/last_screen.json"
FILE_CACHE = "cache/file_sensor/file_cache.json"
CHECK_INTERVAL = 2  # seconds

# Cache last modified times
last_modified = {
    "process": 0,
    "screen": 0,
    "file": 0
}

# Cache last data hashes to avoid duplicate processing
last_data_hash = {
    "process": "",
    "screen": "",
    "file": ""
}

def load_memory_state():
    """Load memory state from file or initialize if not exists"""
    try:
        if os.path.exists(MEMORY_STATE_FILE):
            with open(MEMORY_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            # Initialize with proper structure
            state = {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {
                    "active_window": "",
                    "active_app": "",
                    "active_apps": [],
                    "window_history": [],
                    "screen_text": ""
                },
                "short_term": [],
                "long_term": [],
                "sensor_data": {
                    "screen": {},
                    "process": {},
                    "file": {}
                }
            }
            save_memory_state(state)
            return state
    except Exception as e:
        logger.error(f"Error loading memory state: {e}")
        # Return basic default state on error
        return {
            "version": "1.0",
            "last_update": datetime.now().isoformat(),
            "context": {},
            "short_term": [],
            "long_term": []
        }

def save_memory_state(state):
    """Save memory state to file"""
    try:
        # Create backup of existing file
        # backup_path = f"{MEMORY_STATE_FILE}.bak_{int(time.time())}"
        # shutil.copy2(MEMORY_STATE_FILE, backup_path)
        
        with open(MEMORY_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug("Memory state saved")
        return True
    except Exception as e:
        logger.error(f"Error saving memory state: {e}")
        return False

def compute_data_hash(data):
    """Compute a simple hash of the data to detect changes"""
    try:
        if isinstance(data, dict):
            # Sort keys to ensure consistent hash for same content
            return str(hash(json.dumps(data, sort_keys=True)))
        return str(hash(str(data)))
    except:
        return str(hash(str(data)))

def load_sensor_data(sensor_type):
    """Load sensor data from cache file"""
    try:
        cache_file = None
        if sensor_type == "process":
            cache_file = PROCESS_CACHE
        elif sensor_type == "screen":
            cache_file = SCREEN_CACHE
        elif sensor_type == "file":
            cache_file = FILE_CACHE
        else:
            logger.warning(f"Unknown sensor type: {sensor_type}")
            return None
            
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading {sensor_type} data: {e}")
        return None

def update_context_file(context_data):
    """Update last_context.json with data from sensors"""
    try:
        context = {}
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                context = json.load(f)
                
        # Update timestamp
        context["timestamp"] = int(time.time())
        
        # Update with new context data
        for key, value in context_data.items():
            context[key] = value
            
        # Save updated context
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f, indent=2)
            
        logger.info(f"✅ Updated context file with keys: {list(context_data.keys())}")
        return True
    except Exception as e:
        logger.error(f"Error updating context file: {e}")
        return False

def process_sensor_data(sensor_type, data):
    """Process sensor data and update memory/context"""
    try:
        if not data:
            logger.warning(f"Empty {sensor_type} data received")
            return False
            
        # Compute hash to check if data has changed
        data_hash = compute_data_hash(data)
        if data_hash == last_data_hash[sensor_type]:
            logger.debug(f"{sensor_type.capitalize()} data hasn't changed, skipping update")
            return False
            
        # Update the hash
        last_data_hash[sensor_type] = data_hash
        
        # Load current memory state
        memory_state = load_memory_state()
        
        # Extract context data
        context_data = {}
        
        if sensor_type == "process":
            logger.info(f"Processing process data: {json.dumps(data)[:200]}...")
            
            # Handle different process data formats
            if "active_processes" in data:
                # Format from enhanced_fixed_process_sensor.py
                active_apps = []
                for proc in data.get("active_processes", [])[:10]:  # Get top processes
                    if proc.get("name") and proc.get("name") != "Unknown":
                        active_apps.append(proc.get("name"))
                
                # Try to determine active window and app
                active_window = data.get("active_window", "")
                active_app = data.get("active_app", "")
                
                # If not present, derive from processes
                if not active_app and active_apps:
                    # Use first non-system process as active app
                    system_procs = ["kernel", "launchd", "WindowServer", "systemstats", "logd", "UserEventAgent"]
                    for app in active_apps:
                        if not any(sys_proc in app for sys_proc in system_procs):
                            active_app = app
                            break
                
                context_data = {
                    "active_window": active_window,
                    "active_app": active_app,
                    "active_apps": active_apps
                }
            else:
                # Standard format with direct fields
                context_data = {
                    "active_window": data.get("active_window", ""),
                    "active_app": data.get("active_app", ""),
                    "active_apps": data.get("active_apps", [])
                }
            
            # Handle window history
            window_title = context_data.get("active_window", "")
            if window_title and (
                "window_history" not in memory_state["context"] or 
                not memory_state["context"]["window_history"] or 
                window_title != memory_state["context"]["window_history"][0]
            ):
                window_history = memory_state["context"].get("window_history", [])
                window_history.insert(0, window_title)
                # Keep only the 10 most recent windows
                window_history = window_history[:10]
                context_data["window_history"] = window_history
            
            logger.info(f"Extracted process context: {json.dumps(context_data)}")
                
        elif sensor_type == "screen":
            logger.info(f"Processing screen data: {json.dumps(data)[:200]}...")
            
            # Extract screen text from any format
            screen_text = data.get("screen_text", data.get("text", ""))
            
            # If screen text is empty but we have raw text, use that
            if not screen_text and "raw_text" in data:
                screen_text = data.get("raw_text", "")
            
            context_data = {"screen_text": screen_text}
            
            # Also update window title if available
            if "window_title" in data and data["window_title"]:
                context_data["active_window"] = data["window_title"]
            
            # Update application data if available
            if "application" in data and isinstance(data["application"], dict):
                app_name = data["application"].get("name", "")
                if app_name and app_name != "Unknown Application":
                    context_data["active_app"] = app_name
            
            logger.info(f"Extracted screen context: active_window={context_data.get('active_window', 'None')}, screen_text_length={len(screen_text)}")
                    
        elif sensor_type == "file":
            # File data doesn't directly update the context but is stored in memory state
            logger.info(f"Processing file data: {json.dumps(data)[:200]}...")
            pass
        
        # Ensure we have proper structure
        if "context" not in memory_state:
            memory_state["context"] = {}
            
        # Update memory state
        memory_state["last_update"] = datetime.now().isoformat()
        
        # Update context in memory state
        for key, value in context_data.items():
            memory_state["context"][key] = value
            
        # Store sensor data in appropriate section
        timestamp = datetime.now().isoformat()
        if "sensor_data" not in memory_state:
            memory_state["sensor_data"] = {
                "screen": {},
                "process": {},
                "file": {}
            }
        
        # Ensure sensor_type exists in sensor_data
        if sensor_type not in memory_state["sensor_data"]:
            memory_state["sensor_data"][sensor_type] = {}
            
        memory_state["sensor_data"][sensor_type][timestamp] = data
        
        # Clean up old sensor data (keep only last 20 entries)
        sensor_entries = list(memory_state["sensor_data"][sensor_type].keys())
        if len(sensor_entries) > 20:
            # Sort entries by timestamp and keep the most recent
            sorted_entries = sorted(sensor_entries)
            for old_entry in sorted_entries[:-20]:
                del memory_state["sensor_data"][sensor_type][old_entry]
                
        # Save updated memory state
        save_memory_state(memory_state)
        
        # Update context file
        if context_data:
            update_context_file(context_data)
            
        logger.info(f"✅ Successfully processed {sensor_type} data and updated memory/context")
        return True
    except Exception as e:
        logger.error(f"Error processing {sensor_type} data: {e}")
        logger.error(traceback.format_exc())
        return False

async def check_sensor_updates():
    """Check for updates in sensor cache files"""
    try:
        # Check process sensor
        if os.path.exists(PROCESS_CACHE):
            mod_time = os.path.getmtime(PROCESS_CACHE)
            if mod_time > last_modified["process"]:
                logger.info(f"Detected process sensor update (last: {last_modified['process']}, new: {mod_time})")
                last_modified["process"] = mod_time
                process_data = load_sensor_data("process")
                process_sensor_data("process", process_data)
                
        # Check screen sensor
        if os.path.exists(SCREEN_CACHE):
            mod_time = os.path.getmtime(SCREEN_CACHE)
            if mod_time > last_modified["screen"]:
                logger.info(f"Detected screen sensor update (last: {last_modified['screen']}, new: {mod_time})")
                last_modified["screen"] = mod_time
                screen_data = load_sensor_data("screen")
                process_sensor_data("screen", screen_data)
                
        # Check file sensor
        if os.path.exists(FILE_CACHE):
            mod_time = os.path.getmtime(FILE_CACHE)
            if mod_time > last_modified["file"]:
                logger.info(f"Detected file sensor update (last: {last_modified['file']}, new: {mod_time})")
                last_modified["file"] = mod_time
                file_data = load_sensor_data("file")
                process_sensor_data("file", file_data)
    except Exception as e:
        logger.error(f"Error checking sensor updates: {e}")

async def init_context_file():
    """Initialize context file if it doesn't exist"""
    try:
        if not os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'w') as f:
                json.dump({
                    "timestamp": int(time.time()),
                    "active_window": "",
                    "active_app": "",
                    "active_apps": [],
                    "window_history": [],
                    "screen_text": ""
                }, f, indent=2)
            logger.info("Initialized context file")
    except Exception as e:
        logger.error(f"Error initializing context file: {e}")

async def main():
    """Main function"""
    try:
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/direct_sensor_memory.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info("Starting direct sensor to memory integration")
        
        # Initialize context file if needed
        await init_context_file()
        
        # Initialize last modified times
        if os.path.exists(PROCESS_CACHE):
            last_modified["process"] = os.path.getmtime(PROCESS_CACHE)
        if os.path.exists(SCREEN_CACHE):
            last_modified["screen"] = os.path.getmtime(SCREEN_CACHE)
        if os.path.exists(FILE_CACHE):
            last_modified["file"] = os.path.getmtime(FILE_CACHE)
            
        logger.info(f"Initial modified times: process={last_modified['process']}, screen={last_modified['screen']}, file={last_modified['file']}")
        
        # Process any existing data immediately
        process_data = load_sensor_data("process")
        if process_data:
            process_sensor_data("process", process_data)
            
        screen_data = load_sensor_data("screen")
        if screen_data:
            process_sensor_data("screen", screen_data)
            
        file_data = load_sensor_data("file")
        if file_data:
            process_sensor_data("file", file_data)
            
        # Main loop
        while True:
            await check_sensor_updates()
            await asyncio.sleep(CHECK_INTERVAL)
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Direct sensor to memory integration stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)