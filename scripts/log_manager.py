#!/usr/bin/env python3
"""
Log Manager - Handles log rotation and cleanup for the sensor system

Features:
- Implements TTL (Time To Live) for log files
- Rotates logs when they exceed maximum size
- Keeps a limited number of backup files
- Can be scheduled via cron/systemd timers

Usage:
python3 log_manager.py [--max-age=7] [--max-size=100] [--max-backups=5]
"""

import os
import sys
import time
import glob
import logging
import argparse
import json
import shutil
from datetime import datetime, timedelta

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('log_manager')

# Default settings
DEFAULT_MAX_AGE_DAYS = 7  # Delete logs older than this many days
DEFAULT_MAX_SIZE_MB = 100  # Rotate logs larger than this
DEFAULT_MAX_BACKUPS = 5  # Keep this many rotated logs

class LogManager:
    def __init__(self, max_age_days=DEFAULT_MAX_AGE_DAYS, 
                 max_size_mb=DEFAULT_MAX_SIZE_MB,
                 max_backups=DEFAULT_MAX_BACKUPS):
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self.max_backups = max_backups
        
        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.cache_dir = os.path.join(self.base_dir, 'cache')
        
        logger.info(f"Log manager initialized with: max_age={max_age_days} days, max_size={max_size_mb} MB, max_backups={max_backups}")
    
    def get_file_age_days(self, filepath):
        """Get age of a file in days"""
        if not os.path.exists(filepath):
            return 0
        
        mtime = os.path.getmtime(filepath)
        age_seconds = time.time() - mtime
        return age_seconds / 86400  # Convert to days
    
    def get_file_size_mb(self, filepath):
        """Get size of a file in MB"""
        if not os.path.exists(filepath):
            return 0
        
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)  # Convert to MB
    
    def rotate_log(self, log_file):
        """Rotate a log file when it exceeds max size"""
        if not os.path.exists(log_file):
            return False
        
        # Check if rotation needed
        if self.get_file_size_mb(log_file) < self.max_size_mb:
            return False
        
        logger.info(f"Rotating log file: {log_file}")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{log_file}.{timestamp}"
        
        try:
            # Rotate the file
            shutil.copy2(log_file, backup_file)
            
            # Truncate the original file
            with open(log_file, 'w') as f:
                f.write(f"Log rotated at {datetime.now().isoformat()} - Previous log saved as {os.path.basename(backup_file)}\n")
            
            # Clean up old backups if we have too many
            self.cleanup_old_backups(log_file)
            
            return True
        except Exception as e:
            logger.error(f"Error rotating log {log_file}: {e}")
            return False
    
    def cleanup_old_backups(self, log_file):
        """Remove old backup files keeping only max_backups"""
        try:
            # Find all backup files for this log
            backup_pattern = f"{log_file}.*"
            backup_files = glob.glob(backup_pattern)
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Remove excess backups
            excess_count = len(backup_files) - self.max_backups
            if excess_count > 0:
                for i in range(excess_count):
                    os.remove(backup_files[i])
                    logger.info(f"Removed old backup: {backup_files[i]}")
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def cleanup_old_logs(self):
        """Delete log files older than max_age_days"""
        deleted_count = 0
        total_size_mb = 0
        
        # Process all log files
        for log_dir in ['logs', 'logs/sensors']:
            dir_path = os.path.join(self.base_dir, log_dir)
            if not os.path.exists(dir_path):
                continue
                
            log_files = glob.glob(os.path.join(dir_path, "*.log*"))
            
            for log_file in log_files:
                if self.get_file_age_days(log_file) > self.max_age_days:
                    size_mb = self.get_file_size_mb(log_file)
                    try:
                        os.remove(log_file)
                        logger.info(f"Deleted old log: {log_file} ({size_mb:.2f} MB)")
                        deleted_count += 1
                        total_size_mb += size_mb
                    except Exception as e:
                        logger.error(f"Error deleting {log_file}: {e}")
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} old logs, freed {total_size_mb:.2f} MB")
    
    def cleanup_cache_files(self):
        """Clean up old cache files"""
        cleaned_count = 0
        total_size_mb = 0
        
        # Process sensor cache directories
        for sensor_type in ['file_sensor', 'process_sensor', 'screen_sensor']:
            cache_path = os.path.join(self.cache_dir, sensor_type)
            if not os.path.exists(cache_path):
                continue
                
            # Backup files with timestamp pattern
            backup_files = glob.glob(os.path.join(cache_path, "*.bak_*"))
            
            for cache_file in backup_files:
                if self.get_file_age_days(cache_file) > self.max_age_days / 2:  # More aggressive with cache
                    size_mb = self.get_file_size_mb(cache_file)
                    try:
                        os.remove(cache_file)
                        logger.info(f"Deleted old cache: {cache_file} ({size_mb:.2f} MB)")
                        cleaned_count += 1
                        total_size_mb += size_mb
                    except Exception as e:
                        logger.error(f"Error deleting cache {cache_file}: {e}")
        
        logger.info(f"Cache cleanup complete. Deleted {cleaned_count} old cache files, freed {total_size_mb:.2f} MB")
    
    def process_active_logs(self):
        """Process currently active log files"""
        rotated_count = 0
        
        # Regular logs
        for log_dir in ['logs', 'logs/sensors']:
            dir_path = os.path.join(self.base_dir, log_dir)
            if not os.path.exists(dir_path):
                continue
                
            log_files = glob.glob(os.path.join(dir_path, "*.log"))
            
            for log_file in log_files:
                if self.rotate_log(log_file):
                    rotated_count += 1
        
        logger.info(f"Log rotation complete. Rotated {rotated_count} logs.")
    
    def run(self):
        """Run all log management tasks"""
        logger.info("Starting log management tasks")
        
        # Process active logs first
        self.process_active_logs()
        
        # Cleanup old logs and cache files
        self.cleanup_old_logs()
        self.cleanup_cache_files()
        
        logger.info("Log management completed successfully")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Log Manager for Sensor System')
    parser.add_argument('--max-age', type=int, default=DEFAULT_MAX_AGE_DAYS,
                        help='Maximum age of log files in days')
    parser.add_argument('--max-size', type=int, default=DEFAULT_MAX_SIZE_MB,
                        help='Maximum size of log files in MB')
    parser.add_argument('--max-backups', type=int, default=DEFAULT_MAX_BACKUPS,
                        help='Maximum number of backups to keep for each log')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Create and run the log manager
    manager = LogManager(
        max_age_days=args.max_age,
        max_size_mb=args.max_size,
        max_backups=args.max_backups
    )
    
    manager.run()