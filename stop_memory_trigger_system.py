#!/usr/bin/env python3
"""
Stop Memory Trigger System

This script stops all components of the memory trigger system.
"""

import os
import signal
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stop_memory_trigger")

def get_pid_from_file(pid_file):
    """Get PID from PID file"""
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        return None
    except Exception as e:
        logger.error(f"Error reading PID file {pid_file}: {e}")
        return None

def kill_process(pid, name):
    """Kill a process by PID"""
    try:
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Sent SIGTERM to {name} process (PID: {pid})")
        return True
    except ProcessLookupError:
        logger.warning(f"Process {name} (PID: {pid}) not found")
        return False
    except Exception as e:
        logger.error(f"Error killing {name} process (PID: {pid}): {e}")
        return False

def kill_process_by_command(command):
    """Kill processes by command name"""
    try:
        # Use ps and grep to find processes
        ps_output = subprocess.check_output(
            f"ps aux | grep '{command}' | grep -v grep",
            shell=True,
            text=True
        )
        
        # Extract PIDs
        lines = ps_output.strip().split('\n')
        killed = 0
        
        for line in lines:
            parts = line.split()
            if len(parts) > 1:
                pid = int(parts[1])
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"Sent SIGTERM to process running '{command}' (PID: {pid})")
                    killed += 1
                except Exception as e:
                    logger.error(f"Error killing process (PID: {pid}): {e}")
        
        if killed > 0:
            logger.info(f"Killed {killed} processes running '{command}'")
        else:
            logger.warning(f"No processes found running '{command}'")
            
        return killed > 0
        
    except subprocess.CalledProcessError:
        logger.warning(f"No processes found running '{command}'")
        return False
    except Exception as e:
        logger.error(f"Error finding processes for '{command}': {e}")
        return False

def main():
    """Main function"""
    logger.info("Stopping Memory Trigger System")
    
    # Track if any process was stopped
    any_stopped = False
    
    # Stop memory trigger connector
    connector_pid = get_pid_from_file("pids/memory_trigger_connector.pid")
    if connector_pid:
        if kill_process(connector_pid, "Memory Trigger Connector"):
            any_stopped = True
    else:
        # Try by command name
        if kill_process_by_command("fixed_connect_memory_trigger.py"):
            any_stopped = True
        if kill_process_by_command("connect_memory_trigger.py"):
            any_stopped = True
    
    # Stop WebSocket server
    websocket_pid = get_pid_from_file("pids/memory_trigger_websocket.pid")
    if websocket_pid:
        if kill_process(websocket_pid, "WebSocket Server"):
            any_stopped = True
    else:
        # Try by command name
        if kill_process_by_command("minimal_ws_server.py"):
            any_stopped = True
    
    # Try to find any other memory trigger processes
    if kill_process_by_command("start_memory_trigger_system.py"):
        any_stopped = True
    
    # Remove PID files
    for pid_file in ["pids/memory_trigger_connector.pid", "pids/memory_trigger_websocket.pid"]:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                logger.info(f"Removed PID file: {pid_file}")
            except Exception as e:
                logger.error(f"Error removing PID file {pid_file}: {e}")
    
    if any_stopped:
        logger.info("✅ Memory Trigger System stopped successfully")
    else:
        logger.warning("⚠️ No Memory Trigger System processes found to stop")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Error stopping Memory Trigger System: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)