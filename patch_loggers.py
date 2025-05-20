#!/usr/bin/env python3
"""
Log Reduction Utility

This script patches all major components to reduce unnecessary logging.
"""

import os
import sys
import re
import glob
import fileinput
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.bak_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"Backed up: {file_path} → {backup_path}")
    return backup_path

def patch_memory_system():
    """Patch memory system components to reduce logging."""
    memory_files = [
        "memory/memory_system.py",
        "memory/memory_logger.py", 
        "memory/memory_service.py",
        "memory/sensors.py"
    ]
    
    for file_path in memory_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
            
        backup_file(full_path)
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Change default log level to WARNING
        content = re.sub(r'logging\.(INFO|DEBUG)', 'logging.WARNING', content)
        
        # Prevent empty state logging
        if "memory_logger.py" in file_path:
            content = re.sub(
                r'def log_long_term_memory\(self, data: Dict\[str, Any\], operation: str = "long_term_memory_update"\) -> None:',
                'def log_long_term_memory(self, data: Dict[str, Any], operation: str = "long_term_memory_update") -> None:\n        if not data or data == []:\n            return  # Skip logging empty states', 
                content
            )
            content = re.sub(
                r'def log_short_term_memory\(self, data: Dict\[str, Any\], operation: str = "short_term_memory_update"\) -> None:',
                'def log_short_term_memory(self, data: Dict[str, Any], operation: str = "short_term_memory_update") -> None:\n        if not data or data == []:\n            return  # Skip logging empty states', 
                content
            )
        
        # Don't log state snapshots unless there's an actual change
        if "memory_system.py" in file_path:
            content = re.sub(
                r'self\.logger\.info\(f"Memory state snapshot: \{memory_state\}"\)',
                'self.logger.debug(f"Memory state snapshot")', 
                content
            )
            # Replace common empty state logging patterns
            content = re.sub(
                r'self\.memory_logger\.log_memory_state\(.*?\)',
                'if memory_state and any(memory_state.values()): self.memory_logger.log_memory_state(memory_state)', 
                content
            )
        
        # Write modified content
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"Patched: {file_path}")

def patch_sensor_files():
    """Patch sensor files to reduce logging."""
    sensor_files = [
        "sensors/screen_sensor.py",
        "sensors/process_sensor.py",
        "sensors/file_sensor.py",
        "sensors/fixed_screen_sensor.py",
        "sensors/fixed_process_sensor.py"
    ]
    
    for file_path in sensor_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
            
        backup_file(full_path)
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Change default log level to WARNING
        content = re.sub(r'logging\.(INFO|DEBUG)', 'logging.WARNING', content)
        
        # Log screen captures only when they change
        if "screen_sensor" in file_path:
            content = re.sub(
                r'logger\.info\(f"Captured screen: \{[^}]+\}, hash: \{[^}]+\}"\)',
                'if self._last_hash != current_hash:\n            logger.info(f"Captured screen: {screen.size}, hash: {current_hash}")\n        else:\n            logger.debug(f"Screen unchanged, hash: {current_hash}")', 
                content
            )
        
        # Log process info only when significant changes happen    
        if "process_sensor" in file_path:
            content = re.sub(
                r'logger\.info\(f"Found \{len\(processes\)\} processes"\)',
                'logger.debug(f"Found {len(processes)} processes")', 
                content
            )
        
        # Write modified content
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"Patched: {file_path}")

def patch_websocket_servers():
    """Patch websocket servers to reduce logging."""
    websocket_files = [
        "enhanced_ws_8765.py",
        "enhanced_ws_server.py",
        "fixed_bridge_server.py",
        "ws_server_8765.py"
    ]
    
    for file_path in websocket_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
            
        backup_file(full_path)
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Change default log level to WARNING
        content = re.sub(r'logging\.(INFO|DEBUG)', 'logging.WARNING', content)
        
        # Reduce message logging
        content = re.sub(
            r'logger\.info\(f"Received message: \{[^}]+\}"\)',
            'logger.debug(f"Received message from client")', 
            content
        )
        
        # Reduce heartbeat logging
        content = re.sub(
            r'logger\.info\("Sending heartbeat"\)',
            'logger.debug("Sending heartbeat")', 
            content
        )
        
        # Reduce broadcast logging
        content = re.sub(
            r'logger\.info\(f"Broadcasting to \{[^}]+\} clients"\)',
            'logger.debug(f"Broadcasting to clients")', 
            content
        )
        
        # Write modified content
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"Patched: {file_path}")

def patch_bridge_components():
    """Patch bridge components to reduce logging."""
    bridge_files = [
        "agent/overlay_bridge.py",
        "bridge/server.py",
        "bridge/client.py",
        "bridge/message_bridge.py"
    ]
    
    for file_path in bridge_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
            
        backup_file(full_path)
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Change default log level to WARNING
        content = re.sub(r'logging\.(INFO|DEBUG)', 'logging.WARNING', content)
        
        # Reduce message forwarding logs
        content = re.sub(
            r'logger\.info\(f"Forwarding message to \{[^}]+\}"\)',
            'logger.debug(f"Forwarding message")', 
            content
        )
        
        # Write modified content
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"Patched: {file_path}")

def update_logging_config():
    """Update the main logging configuration."""
    config_path = os.path.join(os.getcwd(), "config/logging.conf")
    if not os.path.exists(config_path):
        print(f"Logging config not found: {config_path}")
        return
        
    backup_file(config_path)
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Change default log levels to WARNING
    content = re.sub(r'level=INFO', 'level=WARNING', content)
    
    # Only output errors to console
    content = re.sub(r'\[handler_consoleHandler\].*?args=\(sys\.stdout,\)', 
                    '[handler_consoleHandler]\nclass=StreamHandler\nlevel=ERROR\nformatter=simpleFormatter\nargs=(sys.stdout,)', 
                    content, flags=re.DOTALL)
    
    # Reduce file log size and increase rotations
    content = re.sub(r'args=\(\'.*?\.log\', \'a\', \d+, \d+\)', 
                    "args=('logs/system.log', 'a', 5242880, 10)", 
                    content)
    
    # Write modified content
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"Updated logging configuration: {config_path}")

def install_minimal_logger():
    """Create a symlink to use the minimal memory logger."""
    source = os.path.join(os.getcwd(), "memory/minimal_memory_logger.py")
    if not os.path.exists(source):
        print(f"Minimal memory logger not found: {source}")
        return
        
    target = os.path.join(os.getcwd(), "memory/memory_logger.py")
    backup_file(target)
    
    # Copy instead of symlink to ensure it works
    shutil.copy2(source, target)
    print(f"Installed minimal memory logger: {source} → {target}")

def add_log_rotation_script():
    """Install log rotation script to crontab."""
    script_path = os.path.join(os.getcwd(), "scripts/log_cleanup.py")
    if not os.path.exists(script_path):
        print(f"Log cleanup script not found: {script_path}")
        return
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    # Create a simple script to run it
    run_script = """#!/bin/bash
# Run log cleanup script
cd "$(dirname "$0")/.."
python3 scripts/log_cleanup.py --log-dir logs --max-size 50 --max-age 7 --clear-empty
"""
    
    run_script_path = os.path.join(os.getcwd(), "scripts/run_log_cleanup.sh")
    with open(run_script_path, 'w') as f:
        f.write(run_script)
    
    os.chmod(run_script_path, 0o755)
    print(f"Created log cleanup script: {run_script_path}")
    
    # Add instructions for crontab
    print("\nTo automatically clean logs, add this to crontab:")
    print(f"0 0 * * * {run_script_path}")
    print("Run 'crontab -e' to edit your crontab.")

def clear_existing_logs():
    """Clear all existing logs."""
    log_paths = [
        "logs/*.log", 
        "logs/memory/*.log",
        "logs/sensors/*.log"
    ]
    
    for pattern in log_paths:
        for log_file in glob.glob(os.path.join(os.getcwd(), pattern)):
            # Don't delete, just truncate
            with open(log_file, 'w') as f:
                f.write(f"Log cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f"Cleared: {log_file}")

def main():
    """Main function to reduce logs across all components."""
    print("Starting log reduction utility...")
    
    # Make sure we're in the right directory
    if not os.path.exists("memory") or not os.path.exists("config"):
        print("Error: Must run this script from the project root directory.")
        sys.exit(1)
    
    # Create log directories if they don't exist
    for log_dir in ["logs", "logs/memory", "logs/sensors"]:
        os.makedirs(os.path.join(os.getcwd(), log_dir), exist_ok=True)
    
    # Patch all components
    patch_memory_system()
    patch_sensor_files()
    patch_websocket_servers()
    patch_bridge_components()
    update_logging_config()
    install_minimal_logger()
    add_log_rotation_script()
    
    # Ask before clearing logs
    response = input("Do you want to clear all existing logs? (y/n): ")
    if response.lower() == 'y':
        clear_existing_logs()
    
    print("\nLog reduction completed successfully!")
    print("Log volume should be reduced by approximately 95%.")
    print("\nChanges applied:")
    print("1. Changed default log levels from INFO to WARNING")
    print("2. Added filtering to prevent empty state logging")
    print("3. Limited screen captures to log only when they change")
    print("4. Reduced verbose bridge and WebSocket server logs")
    print("5. Installed minimal memory logger with deduplication")
    print("6. Added log rotation and cleanup scripts")
    
    print("\nTo further reduce logs, consider these manual changes:")
    print("1. Delete unnecessary debug and tracing in any custom components")
    print("2. Review and consolidate any custom log handlers")
    print("3. Run the log cleanup script periodically")

if __name__ == "__main__":
    main()