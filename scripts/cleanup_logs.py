#!/usr/bin/env python3
"""
Log Cleanup Script
Cleans up and organizes log files.
"""
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
MAX_LOG_AGE_DAYS = 7  # Delete logs older than this
MAX_LOG_SIZE_MB = 10  # Maximum size for individual log files
MAX_TOTAL_LOGS_MB = 1000  # Maximum total size for all logs
LOG_DIRS = [
    'logs/sensors',
    'logs/llm',
    'logs/agent',
    'logs/ui',
    'logs/memory',
    'logs/websocket',
    'logs/bridge',
    'logs/neural_ui',
    'logs/do_button',
    'logs/overlay',
    'logs/backend'
]

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    return os.path.getsize(file_path) / (1024 * 1024)

def get_total_logs_size() -> float:
    """Get total size of all log files in megabytes."""
    total_size = 0
    for log_dir in LOG_DIRS:
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    total_size += get_file_size_mb(os.path.join(log_dir, file))
    return total_size

def cleanup_old_logs():
    """Remove log files older than MAX_LOG_AGE_DAYS."""
    cutoff_date = datetime.now() - timedelta(days=MAX_LOG_AGE_DAYS)
    
    for log_dir in LOG_DIRS:
        if not os.path.exists(log_dir):
            continue
            
        for file in os.listdir(log_dir):
            if not file.endswith('.log'):
                continue
                
            file_path = os.path.join(log_dir, file)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_date:
                try:
                    os.remove(file_path)
                    print(f"Removed old log file: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

def cleanup_large_logs():
    """Remove largest log files if total size exceeds MAX_TOTAL_LOGS_MB."""
    while get_total_logs_size() > MAX_TOTAL_LOGS_MB:
        largest_file = None
        largest_size = 0
        
        for log_dir in LOG_DIRS:
            if not os.path.exists(log_dir):
                continue
                
            for file in os.listdir(log_dir):
                if not file.endswith('.log'):
                    continue
                    
                file_path = os.path.join(log_dir, file)
                size = get_file_size_mb(file_path)
                
                if size > largest_size:
                    largest_size = size
                    largest_file = file_path
        
        if largest_file:
            try:
                os.remove(largest_file)
                print(f"Removed large log file: {largest_file}")
            except Exception as e:
                print(f"Error removing {largest_file}: {e}")
        else:
            break

def organize_logs():
    """Organize log files into appropriate directories."""
    # Create a backup directory for old logs
    backup_dir = f"logs/backup_{int(time.time())}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Move all log files from root logs directory to backup
    logs_dir = 'logs'
    for file in os.listdir(logs_dir):
        if file.endswith('.log') and os.path.isfile(os.path.join(logs_dir, file)):
            try:
                shutil.move(
                    os.path.join(logs_dir, file),
                    os.path.join(backup_dir, file)
                )
                print(f"Moved {file} to backup directory")
            except Exception as e:
                print(f"Error moving {file}: {e}")

def main():
    """Main cleanup function."""
    print("Starting log cleanup...")
    
    # Create necessary directories
    for log_dir in LOG_DIRS:
        os.makedirs(log_dir, exist_ok=True)
    
    # Perform cleanup operations
    cleanup_old_logs()
    cleanup_large_logs()
    organize_logs()
    
    print("Log cleanup completed")

if __name__ == "__main__":
    main() 