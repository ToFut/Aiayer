#!/usr/bin/env python3
"""
Script to update conscious.json with all sensor data
This integrates screen, process, and file sensors into the conscious memory
"""
import json
import os
import glob
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'memory_update.log'), mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory.update")

# Paths - using absolute paths to avoid issues
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
CONSCIOUS_FILE = os.path.join(MEMORY_DIR, "conscious.json")
SCREEN_DATA_DIR = os.path.join(MEMORY_DIR, "screen_data")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
SCREEN_CACHE_FILE = os.path.join(CACHE_DIR, "screen_sensor/last_screen.json")
PROCESS_CACHE_FILE = os.path.join(CACHE_DIR, "process_sensor/process_cache.json")
FILE_CACHE_FILE = os.path.join(CACHE_DIR, "file_sensor/last_file.json")

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file safely"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return {}
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file safely"""
    try:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

def get_latest_screen_data() -> List[Dict[str, Any]]:
    """Get the most recent screen data files"""
    try:
        # First ensure directory exists
        os.makedirs(SCREEN_DATA_DIR, exist_ok=True)
        
        # Get all screen data files
        screen_files = glob.glob(os.path.join(SCREEN_DATA_DIR, "*.json"))
        
        # Sort by modification time (newest first)
        screen_files.sort(key=os.path.getmtime, reverse=True)
        
        # Load data from the 10 most recent files
        screen_data = []
        for file_path in screen_files[:10]:
            data = load_screen_data(file_path)
            if data:
                screen_data.append(data)
        
        # If we have no data from files, try to get from cache
        if not screen_data and os.path.exists(SCREEN_CACHE_FILE):
            data = load_screen_data(SCREEN_CACHE_FILE)
            if data:
                screen_data.append(data)
                
        return screen_data
    except Exception as e:
        logger.error(f"Error getting latest screen data: {e}")
        return []

def load_screen_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load screen data from a file"""
    try:
        data = load_json_file(file_path)
        if not data:
            return None
            
        # Extract relevant fields and ensure they exist
        screen_data = {
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "image_hash": data.get("image_hash", ""),
            "screen_size": data.get("screen_size", [0, 0]),
            "source_file": file_path
        }
        
        # Add formatted datetime if timestamp is a unix timestamp
        if isinstance(screen_data["timestamp"], (int, float)):
            screen_data["datetime"] = datetime.fromtimestamp(screen_data["timestamp"]).isoformat()
        else:
            screen_data["datetime"] = screen_data["timestamp"]
            
        return screen_data
    except Exception as e:
        logger.error(f"Error loading screen data from {file_path}: {e}")
        return None

def load_process_data() -> Optional[Dict[str, Any]]:
    """Load process data from cache file"""
    try:
        data = load_json_file(PROCESS_CACHE_FILE)
        if not data:
            return None
            
        # Extract relevant information
        process_data = {
            "timestamp": data.get("timestamp", time.time()),
            "datetime": datetime.fromtimestamp(data.get("timestamp", time.time())).isoformat(),
            "active_processes": []
        }
        
        # Extract process information
        if "active_processes" in data and isinstance(data["active_processes"], list):
            # Extract top 15 processes, excluding system processes
            top_processes = []
            for proc in data["active_processes"]:
                if isinstance(proc, dict) and "name" in proc:
                    name = proc.get("name", "")
                    # Skip system processes
                    if name.startswith(("kernel", "launchd", "com.apple", "system")):
                        continue
                    
                    # Create a simplified process entry
                    proc_entry = {
                        "name": name,
                        "pid": proc.get("pid", 0),
                        "username": proc.get("username", "")
                    }
                    top_processes.append(proc_entry)
                    
                    if len(top_processes) >= 15:
                        break
                        
            process_data["active_processes"] = top_processes
            
            # Extract just the names for active_apps list
            process_data["active_apps"] = [p.get("name", "") for p in top_processes if p.get("name")]
            
        return process_data
    except Exception as e:
        logger.error(f"Error loading process data: {e}")
        return None

def load_file_data() -> Optional[Dict[str, Any]]:
    """Load file data from cache file"""
    try:
        data = load_json_file(FILE_CACHE_FILE)
        if not data:
            return None
            
        # Create a properly structured entry
        file_data = {
            "timestamp": data.get("timestamp", time.time()),
            "datetime": datetime.fromtimestamp(data.get("timestamp", time.time())).isoformat(),
            "events": data.get("events", []),
            "event_count": data.get("event_count", 0)
        }
        
        return file_data
    except Exception as e:
        logger.error(f"Error loading file data: {e}")
        return None

def generate_screen_insight(screen_data: Dict[str, Any]) -> str:
    """Generate an insight based on screen data"""
    if not screen_data:
        return "No screen data available"
        
    # Extract image hash and timestamp
    image_hash = screen_data.get("image_hash", "unknown")
    timestamp = screen_data.get("datetime", datetime.now().isoformat())
    screen_size = screen_data.get("screen_size", [0, 0])
    
    return f"Screen capture at {timestamp} with resolution {screen_size[0]}x{screen_size[1]} (hash: {image_hash[:8]})"

def generate_process_insight(process_data: Dict[str, Any]) -> str:
    """Generate an insight based on process data"""
    if not process_data:
        return "No process data available"
        
    # Extract active apps
    active_apps = process_data.get("active_apps", [])
    timestamp = process_data.get("datetime", datetime.now().isoformat())
    
    if not active_apps:
        return f"No significant active processes detected at {timestamp}"
    
    # Limit to top 5 for the insight
    top_apps = active_apps[:5]
    remaining = len(active_apps) - len(top_apps)
    
    insight = f"Active applications at {timestamp}: {', '.join(top_apps)}"
    if remaining > 0:
        insight += f" and {remaining} more"
    
    return insight

def generate_file_insight(file_data: Dict[str, Any]) -> str:
    """Generate an insight based on file data"""
    if not file_data:
        return "No file data available"
        
    timestamp = file_data.get("datetime", datetime.now().isoformat())
    events = file_data.get("events", [])
    event_count = file_data.get("event_count", 0) or len(events)
    
    if not events:
        return f"No file system events detected at {timestamp}"
    
    return f"Detected {event_count} file system events at {timestamp}"

def generate_integrated_insight(
    screen_data: Optional[Dict[str, Any]],
    process_data: Optional[Dict[str, Any]],
    file_data: Optional[Dict[str, Any]]
) -> str:
    """Generate an integrated insight from all sensor data"""
    timestamp = datetime.now().isoformat()
    
    # Extract key information from each sensor
    active_apps = process_data.get("active_apps", [])[:3] if process_data else []
    screen_hash = screen_data.get("image_hash", "")[:8] if screen_data else ""
    file_events = len(file_data.get("events", [])) if file_data else 0
    
    # Create integrated insight
    parts = []
    
    if active_apps:
        parts.append(f"Running: {', '.join(active_apps)}")
    
    if screen_hash:
        parts.append(f"Screen: {screen_hash}")
    
    if file_events > 0:
        parts.append(f"Files: {file_events} events")
    
    if parts:
        return f"System state at {timestamp}: {'; '.join(parts)}"
    else:
        return f"System idle at {timestamp}"

def generate_llm_prompt(conscious: Dict[str, Any]) -> str:
    """Generate a prompt for an LLM based on the conscious memory"""
    timestamp = datetime.now().isoformat()
    
    prompt = f"# System Context Analysis\nTimestamp: {timestamp}\n\n"
    
    # Add recent insights
    if "insights" in conscious and conscious["insights"]:
        prompt += "## Recent Insights\n"
        for i, insight in enumerate(conscious["insights"][:5]):
            prompt += f"{i+1}. {insight.get('content', '')}\n"
        prompt += "\n"
    
    # Add active applications
    process_buffer = conscious.get("sensor_buffers", {}).get("process", [])
    if process_buffer:
        prompt += "## Active Applications\n"
        for process_data in process_buffer[:1]:  # Just use the most recent
            active_apps = process_data.get("active_apps", [])
            if active_apps:
                for app in active_apps[:10]:
                    prompt += f"- {app}\n"
            else:
                prompt += "- No significant applications detected\n"
        prompt += "\n"
    
    # Add file activity
    file_buffer = conscious.get("sensor_buffers", {}).get("file", [])
    if file_buffer:
        prompt += "## Recent File Activity\n"
        for file_data in file_buffer[:1]:  # Just use the most recent
            events = file_data.get("events", [])
            if events:
                for event in events[:5]:
                    if isinstance(event, dict) and "path" in event:
                        path = event.get("path", "")
                        event_type = event.get("type", "modified")
                        prompt += f"- {event_type}: {path}\n"
                    elif isinstance(event, str):
                        prompt += f"- {event}\n"
            else:
                prompt += "- No recent file activity\n"
        prompt += "\n"
    
    # Add analysis request
    prompt += "## Analysis Request\n"
    prompt += "Please analyze the user's current context and provide the following:\n\n"
    prompt += "1. What is the user currently working on?\n"
    prompt += "2. What tools or applications are they using?\n"
    prompt += "3. What might they need help with based on this context?\n"
    prompt += "4. Are there any patterns or trends in their recent activity?\n"
    
    return prompt

def update_conscious_memory():
    """Update the conscious memory with the latest sensor data"""
    try:
        # Create screen data directory if it doesn't exist
        os.makedirs(SCREEN_DATA_DIR, exist_ok=True)
        
        # Load existing conscious memory or create default structure
        if os.path.exists(CONSCIOUS_FILE):
            conscious = load_json_file(CONSCIOUS_FILE)
        else:
            # Create a default structure if file doesn't exist
            conscious = {
                "timestamp": datetime.now().isoformat(),
                "sensor_buffers": {
                    "screen": [],
                    "process": [],
                    "file": []
                },
                "system_state": {
                    "last_update": datetime.now().isoformat(),
                    "last_insight_generation": None
                },
                "insights": []
            }
        
        # Get the latest screen data
        screen_data = None
        if os.path.exists(SCREEN_CACHE_FILE):
            screen_data = load_screen_data(SCREEN_CACHE_FILE)
            if screen_data:
                # Add to the screen buffer
                conscious["sensor_buffers"]["screen"].insert(0, screen_data)
                # Keep only the 10 most recent entries
                conscious["sensor_buffers"]["screen"] = conscious["sensor_buffers"]["screen"][:10]
        
        # Load process data
        process_data = load_process_data()
        if process_data:
            # Add to the process buffer
            conscious["sensor_buffers"]["process"].insert(0, process_data)
            # Keep only the 10 most recent entries
            conscious["sensor_buffers"]["process"] = conscious["sensor_buffers"]["process"][:10]
        
        # Load file data
        file_data = load_file_data()
        if file_data:
            # Add to the file buffer
            conscious["sensor_buffers"]["file"].insert(0, file_data)
            # Keep only the 10 most recent entries
            conscious["sensor_buffers"]["file"] = conscious["sensor_buffers"]["file"][:10]
        
        # Update timestamp
        current_time = datetime.now().isoformat()
        conscious["timestamp"] = current_time
        conscious["system_state"]["last_update"] = current_time
        
        # Generate insights based on the sensor data
        insights = []
        
        # Screen insight
        if screen_data:
            screen_insight = {
                "timestamp": current_time,
                "content": generate_screen_insight(screen_data),
                "type": "screen"
            }
            insights.append(screen_insight)
        
        # Process insight
        if process_data:
            process_insight = {
                "timestamp": current_time,
                "content": generate_process_insight(process_data),
                "type": "process"
            }
            insights.append(process_insight)
        
        # File insight
        if file_data:
            file_insight = {
                "timestamp": current_time,
                "content": generate_file_insight(file_data),
                "type": "file"
            }
            insights.append(file_insight)
        
        # Integrated insight
        integrated_insight = {
            "timestamp": current_time,
            "content": generate_integrated_insight(screen_data, process_data, file_data),
            "type": "integrated"
        }
        insights.append(integrated_insight)
        
        # Add new insights
        if "insights" not in conscious:
            conscious["insights"] = []
            
        # Add new insights at the beginning
        for insight in insights:
            conscious["insights"].insert(0, insight)
            
        # Limit to 20 insights
        conscious["insights"] = conscious["insights"][:20]
        
        # Update last insight generation time
        conscious["system_state"]["last_insight_generation"] = current_time
        
        # Save the updated conscious memory
        save_success = save_json_file(CONSCIOUS_FILE, conscious)
        
        if save_success:
            logger.info(f"Updated conscious memory with {1 if screen_data else 0} screen entry, " +
                  f"{1 if process_data else 0} process entry, " +
                  f"{1 if file_data else 0} file entry")
            return conscious
        else:
            logger.error("Failed to save conscious memory file")
            return None
        
    except Exception as e:
        logger.error(f"Error updating conscious memory: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    logger.info("Starting conscious memory update")
    conscious = update_conscious_memory()
    
    if conscious:
        # Generate a prompt that could be sent to an LLM
        prompt = generate_llm_prompt(conscious)
        logger.info("Generated LLM prompt that could be used for further analysis")
        logger.debug(f"LLM Prompt: {prompt}")
    
    logger.info("Finished conscious memory update")