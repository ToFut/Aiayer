#!/usr/bin/env python3
"""
Cache Cleanup Manager

- Implements cache size limits to prevent disk overflow
- Removes old cache files after size limit is exceeded
- Enables sensor system to operate for extended periods

Usage: 
python3 cleanup_manager.py --max-cache-mb=500 --max-logs-mb=200
"""

import os
import sys
import glob
import json
import argparse
import logging
import shutil
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cleanup_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cleanup_manager')

# Default settings
DEFAULT_MAX_CACHE_MB = 500  # Maximum cache size in MB
DEFAULT_MAX_LOGS_MB = 200   # Maximum logs size in MB
DEFAULT_RESERVED_MB = 1000  # Minimum free disk space in MB

class CleanupManager:
    def __init__(self, max_cache_mb=DEFAULT_MAX_CACHE_MB, 
                 max_logs_mb=DEFAULT_MAX_LOGS_MB,
                 reserved_mb=DEFAULT_RESERVED_MB):
        self.max_cache_mb = max_cache_mb
        self.max_logs_mb = max_logs_mb
        self.reserved_mb = reserved_mb
        
        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(self.base_dir, 'cache')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        
        logger.info(f"Cleanup manager initialized with: max_cache={max_cache_mb}MB, "
                   f"max_logs={max_logs_mb}MB, reserved_space={reserved_mb}MB")
    
    def get_directory_size_mb(self, directory):
        """Get the size of a directory in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def get_free_space_mb(self):
        """Get free disk space in MB"""
        if hasattr(os, 'statvfs'):  # UNIX/Linux/MacOS
            statvfs = os.statvfs(self.base_dir)
            return (statvfs.f_frsize * statvfs.f_bavail) / (1024 * 1024)
        else:  # Windows
            try:
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(self.base_dir), 
                                                          None, None, 
                                                          ctypes.pointer(free_bytes))
                return free_bytes.value / (1024 * 1024)
            except:
                logger.warning("Could not determine free disk space. Assuming sufficient space.")
                return self.reserved_mb + 1000  # Assume enough space
    
    def cleanup_cache_directory(self, cache_type):
        """Clean up a specific cache directory based on age and size limit"""
        cache_path = os.path.join(self.cache_dir, cache_type)
        if not os.path.exists(cache_path):
            logger.warning(f"Cache directory does not exist: {cache_path}")
            return 0
        
        # Get current size
        current_size_mb = self.get_directory_size_mb(cache_path)
        logger.info(f"Current {cache_type} cache size: {current_size_mb:.2f}MB")
        
        # Check if cleanup needed
        if current_size_mb <= self.max_cache_mb / 3:  # Divide by 3 as we have 3 sensor types
            logger.info(f"No cleanup needed for {cache_type}")
            return 0
        
        # Find backup files
        backup_files = []
        for ext in ["*.bak_*", "*.json.bak_*"]:
            backup_files.extend(glob.glob(os.path.join(cache_path, ext)))
        
        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Calculate target size (75% of max to leave some buffer)
        target_size_mb = self.max_cache_mb * 0.75 / 3
        
        # Remove files until target size is reached
        removed_count = 0
        removed_size_mb = 0
        
        for backup_file in backup_files:
            if current_size_mb <= target_size_mb:
                break
                
            try:
                file_size_mb = os.path.getsize(backup_file) / (1024 * 1024)
                os.remove(backup_file)
                current_size_mb -= file_size_mb
                removed_size_mb += file_size_mb
                removed_count += 1
                logger.debug(f"Removed {backup_file}, freed {file_size_mb:.2f}MB")
            except Exception as e:
                logger.error(f"Error removing file {backup_file}: {e}")
        
        logger.info(f"Removed {removed_count} files from {cache_type} cache, "
                   f"freed {removed_size_mb:.2f}MB")
        return removed_size_mb
    
    def cleanup_logs(self):
        """Clean up log files based on age and size limit"""
        if not os.path.exists(self.logs_dir):
            logger.warning(f"Logs directory does not exist: {self.logs_dir}")
            return 0
        
        # Get current size
        current_size_mb = self.get_directory_size_mb(self.logs_dir)
        logger.info(f"Current logs size: {current_size_mb:.2f}MB")
        
        # Check if cleanup needed
        if current_size_mb <= self.max_logs_mb:
            logger.info("No cleanup needed for logs")
            return 0
        
        # Find log files recursively
        log_files = []
        for ext in ["*.log.*", "*.log"]:
            for root, dirs, files in os.walk(self.logs_dir):
                for pattern in [ext]:
                    log_files.extend(glob.glob(os.path.join(root, pattern)))
        
        # Sort by modification time (oldest first)
        log_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Calculate target size (75% of max to leave some buffer)
        target_size_mb = self.max_logs_mb * 0.75
        
        # Remove files until target size is reached
        removed_count = 0
        removed_size_mb = 0
        
        for log_file in log_files:
            if current_size_mb <= target_size_mb:
                break
                
            # Don't remove currently active log files
            if log_file.endswith(".log") and "." not in os.path.basename(log_file):
                continue
                
            try:
                file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
                os.remove(log_file)
                current_size_mb -= file_size_mb
                removed_size_mb += file_size_mb
                removed_count += 1
                logger.debug(f"Removed {log_file}, freed {file_size_mb:.2f}MB")
            except Exception as e:
                logger.error(f"Error removing file {log_file}: {e}")
        
        logger.info(f"Removed {removed_count} log files, freed {removed_size_mb:.2f}MB")
        return removed_size_mb
    
    def check_disk_space(self):
        """Check if disk space is running low and perform emergency cleanup if needed"""
        free_space_mb = self.get_free_space_mb()
        logger.info(f"Current free disk space: {free_space_mb:.2f}MB")
        
        if free_space_mb >= self.reserved_mb:
            logger.info("Sufficient disk space available")
            return True
        
        logger.warning(f"Low disk space: {free_space_mb:.2f}MB free, {self.reserved_mb}MB required")
        
        # Emergency cleanup - remove all backup files
        total_freed = 0
        
        # Clean cache directories
        for cache_type in ["file_sensor", "process_sensor", "screen_sensor"]:
            cache_path = os.path.join(self.cache_dir, cache_type)
            if os.path.exists(cache_path):
                backup_files = []
                for ext in ["*.bak_*", "*.json.bak_*"]:
                    backup_files.extend(glob.glob(os.path.join(cache_path, ext)))
                
                for backup_file in backup_files:
                    try:
                        file_size_mb = os.path.getsize(backup_file) / (1024 * 1024)
                        os.remove(backup_file)
                        total_freed += file_size_mb
                        logger.debug(f"Emergency removal: {backup_file}, freed {file_size_mb:.2f}MB")
                    except Exception as e:
                        logger.error(f"Error in emergency removal of {backup_file}: {e}")
        
        # Clean old log files
        for root, dirs, files in os.walk(self.logs_dir):
            for file in files:
                if file.endswith((".log.old", ".log.1", ".log.2")):
                    log_file = os.path.join(root, file)
                    try:
                        file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
                        os.remove(log_file)
                        total_freed += file_size_mb
                        logger.debug(f"Emergency removal: {log_file}, freed {file_size_mb:.2f}MB")
                    except Exception as e:
                        logger.error(f"Error in emergency removal of {log_file}: {e}")
        
        logger.warning(f"Emergency cleanup freed {total_freed:.2f}MB")
        
        # Check if we now have enough space
        free_space_mb = self.get_free_space_mb()
        logger.info(f"Free disk space after emergency cleanup: {free_space_mb:.2f}MB")
        
        return free_space_mb >= self.reserved_mb
    
    def cleanup_change_tracking(self):
        """Clean up sensor change tracking information to limit memory usage"""
        try:
            # Limit the number of tracked changes in screen_sensor cache
            screen_cache_file = os.path.join(self.cache_dir, "screen_sensor", "screen_cache.json")
            if os.path.exists(screen_cache_file):
                try:
                    with open(screen_cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # Limit tracking data
                    if 'changes' in data and len(data['changes']) > 20:
                        data['changes'] = data['changes'][-20:]
                        
                    with open(screen_cache_file, 'w') as f:
                        json.dump(data, f)
                        
                    logger.info(f"Optimized screen sensor change tracking data")
                except Exception as e:
                    logger.error(f"Error optimizing screen cache: {e}")
            
            # Limit the number of tracked processes in process_sensor cache
            process_cache_file = os.path.join(self.cache_dir, "process_sensor", "process_cache.json")
            if os.path.exists(process_cache_file):
                try:
                    with open(process_cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # Limit historical data
                    if 'history' in data and len(data['history']) > 10:
                        data['history'] = data['history'][-10:]
                        
                    with open(process_cache_file, 'w') as f:
                        json.dump(data, f)
                        
                    logger.info(f"Optimized process sensor history data")
                except Exception as e:
                    logger.error(f"Error optimizing process cache: {e}")
                    
        except Exception as e:
            logger.error(f"Error in cleanup_change_tracking: {e}")
    
    def run(self):
        """Run the cache and log cleanup operations"""
        logger.info("Starting cleanup manager")
        
        # Check disk space first
        self.check_disk_space()
        
        # Clean up cache directories
        total_freed_mb = 0
        for cache_type in ["file_sensor", "process_sensor", "screen_sensor"]:
            freed_mb = self.cleanup_cache_directory(cache_type)
            total_freed_mb += freed_mb
        
        # Clean up logs
        freed_mb = self.cleanup_logs()
        total_freed_mb += freed_mb
        
        # Optimize memory usage
        self.cleanup_change_tracking()
        
        # Final disk space check
        self.check_disk_space()
        
        logger.info(f"Cleanup completed. Total space freed: {total_freed_mb:.2f}MB")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Cache and Log Cleanup Manager')
    parser.add_argument('--max-cache-mb', type=int, default=DEFAULT_MAX_CACHE_MB,
                        help='Maximum cache size in MB')
    parser.add_argument('--max-logs-mb', type=int, default=DEFAULT_MAX_LOGS_MB,
                        help='Maximum logs size in MB')
    parser.add_argument('--reserved-mb', type=int, default=DEFAULT_RESERVED_MB,
                        help='Minimum free disk space in MB')
    return parser.parse_args()

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    args = parse_args()
    
    # Create and run the cleanup manager
    cleanup = CleanupManager(
        max_cache_mb=args.max_cache_mb,
        max_logs_mb=args.max_logs_mb,
        reserved_mb=args.reserved_mb
    )
    
    cleanup.run()