import json
import os
import time
import logging
import sys
from datetime import datetime

# Setup directories
os.makedirs('logs/memory', exist_ok=True)
os.makedirs('memory', exist_ok=True)
os.makedirs('pids', exist_ok=True)
os.makedirs('cache', exist_ok=True)
os.makedirs('cache/screen_sensor', exist_ok=True)
os.makedirs('cache/process_sensor', exist_ok=True)
os.makedirs('cache/file_sensor', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_connector')

# Initialize memory state
def init_memory_state():
    """Initialize empty memory state"""
    return {
        "version": "1.0",
        "last_update": datetime.now().isoformat(),
        "context": {},
        "short_term": [],
        "long_term": [],
        "sensor_data": {
            "screen": {},
            "process": {},
            "file": {}
        }
    }

def save_memory_state(state):
    """Save memory state to file"""
    try:
        with open('memory/memory_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving memory state: {e}")
        return False

def load_memory_state():
    """Load memory state from file or initialize if not exists"""
    try:
        with open('memory/memory_state.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Memory state file issue: {e}, creating new state")
        new_state = init_memory_state()
        save_memory_state(new_state)
        return new_state

def save_pid():
    """Save PID to file"""
    try:
        with open('pids/memory_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Error saving PID: {e}")
        return False

def init_sensor_cache(sensor_type):
    """Initialize sensor cache file if it doesn't exist"""
    cache_file = f"cache/{sensor_type}_sensor/{sensor_type}_cache.json"
    if not os.path.exists(cache_file):
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }, f, indent=2)
            logger.info(f"Initialized cache file for {sensor_type} sensor")
        except Exception as e:
            logger.error(f"Error initializing cache file for {sensor_type} sensor: {e}")

def read_sensor_data(sensor_type):
    """Read sensor data from cache files"""
    try:
        cache_file = f"cache/{sensor_type}_sensor/{sensor_type}_cache.json"
        if os.path.exists(cache_file):
            logger.debug(f"Reading {sensor_type} sensor data from {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Cache file for {sensor_type} not found: {cache_file}")
            init_sensor_cache(sensor_type)  # Initialize cache file if missing
            return None
    except Exception as e:
        logger.error(f"Error reading {sensor_type} sensor data: {e}")
        return None

def run_memory_connector():
    """Main memory connector loop"""
    logger.info("Starting memory connector with sensor integration")
    
    # Save PID
    if not save_pid():
        logger.error("Failed to save PID, exiting")
        sys.exit(1)
    
    # Initialize cache files for all sensor types
    for sensor_type in ["screen", "process", "file"]:
        init_sensor_cache(sensor_type)
    
    # Initial memory state
    try:
        memory_state = load_memory_state()
        
        # Initialize sensor data section if not exists
        if "sensor_data" not in memory_state:
            memory_state["sensor_data"] = {
                "screen": {},
                "process": {},
                "file": {}
            }
            
    except Exception as e:
        logger.error(f"Failed to initialize memory state: {e}")
        sys.exit(1)
    
    # Monitor loop
    try:
        while True:
            # Update timestamp
            current_time = datetime.now().isoformat()
            memory_state["last_update"] = current_time
            
            # Read and integrate sensor data
            for sensor_type in ["screen", "process", "file"]:
                try:
                    sensor_data = read_sensor_data(sensor_type)
                    if sensor_data:
                        logger.info(f"Integrating {sensor_type} sensor data into memory")
                        
                        # Add to sensor data with timestamp as key
                        memory_state["sensor_data"][sensor_type][current_time] = sensor_data
                        
                        # Keep only the last 20 entries
                        sensor_entries = list(memory_state["sensor_data"][sensor_type].keys())
                        if len(sensor_entries) > 20:
                            # Sort entries by timestamp and keep the most recent
                            sorted_entries = sorted(sensor_entries)
                            for old_entry in sorted_entries[:-20]:
                                del memory_state["sensor_data"][sensor_type][old_entry]
                            
                        logger.debug(f"Added {sensor_type} data to memory, now has {len(memory_state['sensor_data'][sensor_type])} entries")
                except Exception as e:
                    logger.error(f"Error processing {sensor_type} sensor data: {e}")
            
            # Save updated state
            if save_memory_state(memory_state):
                logger.info(f"Memory state updated with sensor data at {current_time}")
            
            # Sleep to avoid high CPU usage
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in memory connector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_memory_connector()
