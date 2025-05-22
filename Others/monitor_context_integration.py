#!/usr/bin/env python3
"""
Context Integration Monitor

This script continuously monitors the context integration system:
1. Checks if memory files are being updated with sensor data
2. Verifies data flow from sensors to memory
3. Alerts on any issues with context integration
"""
import json
import os
import time
import logging
import traceback
import asyncio
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs/monitoring', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring/context_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('context_monitor')

# Configuration
MEMORY_STATE_FILE = "memory/memory_state.json"
CONTEXT_FILE = "memory/last_context.json"
PROCESS_CACHE = "cache/process_sensor/process_cache.json"
SCREEN_CACHE = "cache/screen_sensor/last_screen.json"
FILE_CACHE = "cache/file_sensor/file_cache.json"
CHECK_INTERVAL = 30  # seconds
ALERT_THRESHOLD = 120  # seconds (alert if no updates for 2 minutes)

# Track last observed update times
last_update_times = {
    "memory_state": 0,
    "context_file": 0,
    "process_cache": 0,
    "screen_cache": 0
}

# Track modification times
last_mod_times = {
    "memory_state": 0,
    "context_file": 0,
    "process_cache": 0,
    "screen_cache": 0
}

# System status
system_healthy = True

def get_file_age(file_path):
    """Get file age in seconds"""
    try:
        if os.path.exists(file_path):
            mod_time = os.path.getmtime(file_path)
            return int(time.time() - mod_time)
        return -1
    except Exception as e:
        logger.error(f"Error getting file age for {file_path}: {e}")
        return -1

def get_context_data():
    """Get current context data"""
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error reading context file: {e}")
        return None

def get_memory_state():
    """Get current memory state"""
    try:
        if os.path.exists(MEMORY_STATE_FILE):
            with open(MEMORY_STATE_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error reading memory state: {e}")
        return None

def get_process_data():
    """Get current process sensor data"""
    try:
        if os.path.exists(PROCESS_CACHE):
            with open(PROCESS_CACHE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error reading process cache: {e}")
        return None

def check_data_flow():
    """Check data flow from sensors to memory"""
    try:
        global system_healthy, last_mod_times
        
        # Check file modification times
        current_mod_times = {
            "memory_state": os.path.getmtime(MEMORY_STATE_FILE) if os.path.exists(MEMORY_STATE_FILE) else 0,
            "context_file": os.path.getmtime(CONTEXT_FILE) if os.path.exists(CONTEXT_FILE) else 0,
            "process_cache": os.path.getmtime(PROCESS_CACHE) if os.path.exists(PROCESS_CACHE) else 0,
            "screen_cache": os.path.getmtime(SCREEN_CACHE) if os.path.exists(SCREEN_CACHE) else 0
        }
        
        # Check if files have been modified
        files_updated = {}
        for file_key, mod_time in current_mod_times.items():
            if mod_time > last_mod_times[file_key]:
                files_updated[file_key] = True
                last_mod_times[file_key] = mod_time
            else:
                files_updated[file_key] = False
        
        # Get file ages
        file_ages = {
            "memory_state": get_file_age(MEMORY_STATE_FILE),
            "context_file": get_file_age(CONTEXT_FILE),
            "process_cache": get_file_age(PROCESS_CACHE),
            "screen_cache": get_file_age(SCREEN_CACHE)
        }
        
        # Get data from files
        context_data = get_context_data()
        memory_state = get_memory_state()
        process_data = get_process_data()
        
        # Check if process data is flowing to context
        process_to_context_flow = False
        if context_data and process_data:
            if context_data.get("active_app") == process_data.get("active_app"):
                process_to_context_flow = True
        
        # Check if context data is in memory state
        context_to_memory_flow = False
        if memory_state and context_data:
            memory_context = memory_state.get("context", {})
            if memory_context.get("active_app") == context_data.get("active_app"):
                context_to_memory_flow = True
        
        # Check system health
        alerts = []
        
        # Alert if files are too old (not updated recently)
        for file_name, age in file_ages.items():
            if age > ALERT_THRESHOLD and age != -1:
                alerts.append(f"{file_name} hasn't been updated in {age} seconds (threshold: {ALERT_THRESHOLD}s)")
        
        # Alert if data flow is broken
        if not process_to_context_flow and file_ages["process_cache"] < ALERT_THRESHOLD:
            alerts.append("Process sensor data is not flowing to context file")
        
        if not context_to_memory_flow and file_ages["context_file"] < ALERT_THRESHOLD:
            alerts.append("Context data is not flowing to memory state")
            
        # Check if we need to update the system health status
        was_healthy = system_healthy
        system_healthy = len(alerts) == 0
        
        # Report status
        if system_healthy:
            if not was_healthy:
                logger.info("✅ System has recovered and is now healthy")
            else:
                logger.info("✅ Context integration system is healthy")
                
            # Log which files were updated this cycle
            updated_files = [k for k, v in files_updated.items() if v]
            if updated_files:
                logger.info(f"Files updated in this cycle: {', '.join(updated_files)}")
            else:
                logger.debug("No files were updated in this cycle")
        else:
            # Log alerts
            logger.warning("⚠️ Context integration issues detected:")
            for alert in alerts:
                logger.warning(f"  - {alert}")
            
        # Return report data
        return {
            "healthy": system_healthy,
            "file_ages": file_ages,
            "files_updated": files_updated,
            "process_to_context_flow": process_to_context_flow,
            "context_to_memory_flow": context_to_memory_flow,
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error checking data flow: {e}")
        logger.error(traceback.format_exc())
        return {
            "healthy": False,
            "error": str(e),
            "alerts": ["Monitor encountered an error during check"]
        }

def print_system_status():
    """Print detailed system status"""
    try:
        # Get ages of key files
        memory_age = get_file_age(MEMORY_STATE_FILE)
        context_age = get_file_age(CONTEXT_FILE)
        process_age = get_file_age(PROCESS_CACHE)
        screen_age = get_file_age(SCREEN_CACHE)
        
        # Get file sizes
        memory_size = os.path.getsize(MEMORY_STATE_FILE) if os.path.exists(MEMORY_STATE_FILE) else 0
        context_size = os.path.getsize(CONTEXT_FILE) if os.path.exists(CONTEXT_FILE) else 0
        
        # Get data
        context_data = get_context_data()
        memory_state = get_memory_state()
        
        # Print status
        logger.info("===== CONTEXT INTEGRATION SYSTEM STATUS =====")
        logger.info(f"File Ages (seconds since last update):")
        logger.info(f"  - Memory State: {memory_age}s {'✅' if memory_age < ALERT_THRESHOLD else '❌'}")
        logger.info(f"  - Context File: {context_age}s {'✅' if context_age < ALERT_THRESHOLD else '❌'}")
        logger.info(f"  - Process Cache: {process_age}s {'✅' if process_age < ALERT_THRESHOLD else '❌'}")
        logger.info(f"  - Screen Cache: {screen_age}s {'✅' if screen_age < ALERT_THRESHOLD else '❌'}")
        
        logger.info(f"File Sizes:")
        logger.info(f"  - Memory State: {memory_size} bytes {'✅' if memory_size > 200 else '❌'}")
        logger.info(f"  - Context File: {context_size} bytes {'✅' if context_size > 200 else '❌'}")
        
        # Show active context
        if context_data:
            logger.info("Current Context:")
            logger.info(f"  - Active App: {context_data.get('active_app', 'N/A')}")
            logger.info(f"  - Active Window: {context_data.get('active_window', 'N/A')}")
            logger.info(f"  - Active Apps Count: {len(context_data.get('active_apps', []))}")
            logger.info(f"  - Window History Count: {len(context_data.get('window_history', []))}")
            logger.info(f"  - Screen Text Length: {len(context_data.get('screen_text', ''))}")
        else:
            logger.warning("  - Context data not available")
        
        # Overall status
        if system_healthy:
            logger.info("✅ OVERALL STATUS: HEALTHY - All components functioning properly")
        else:
            logger.warning("⚠️ OVERALL STATUS: ISSUES DETECTED - Check alerts above")
    except Exception as e:
        logger.error(f"Error printing system status: {e}")

async def run_monitor():
    """Run the monitoring loop"""
    try:
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/context_monitor.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info("Starting context integration monitoring")
        
        # Initialize mod times
        if os.path.exists(MEMORY_STATE_FILE):
            last_mod_times["memory_state"] = os.path.getmtime(MEMORY_STATE_FILE)
        if os.path.exists(CONTEXT_FILE):
            last_mod_times["context_file"] = os.path.getmtime(CONTEXT_FILE)
        if os.path.exists(PROCESS_CACHE):
            last_mod_times["process_cache"] = os.path.getmtime(PROCESS_CACHE)
        if os.path.exists(SCREEN_CACHE):
            last_mod_times["screen_cache"] = os.path.getmtime(SCREEN_CACHE)
        
        # Run initial check
        print_system_status()
        
        # Monitor loop
        check_count = 0
        while True:
            # Check data flow
            check_data_flow()
            
            # Every 5 checks (or roughly every 2.5 minutes), print a detailed status
            check_count += 1
            if check_count % 5 == 0:
                print_system_status()
                check_count = 0
            
            # Wait for next check
            await asyncio.sleep(CHECK_INTERVAL)
    
    except Exception as e:
        logger.error(f"Error in monitor function: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        logger.info("Context integration monitor stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)