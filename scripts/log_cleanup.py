#!/usr/bin/env python3
"""
Log cleanup script for managing log files and directories.
Handles log rotation, size limits, and age-based cleanup.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
import glob
import shutil
import tarfile
import gzip

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_directory_size(path):
    """Calculate total size of a directory in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)  # Convert to MB

def cleanup_old_logs(log_dir, max_age_days):
    """Remove log files older than max_age_days."""
    logger = setup_logging()
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    count = 0
    
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if file.endswith('.log') or file.endswith('.gz'):
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    if count > 0:
        logger.info(f"Removed {count} old log files")

def compress_large_logs(log_dir, max_size_mb):
    """Compress log files larger than max_size_mb."""
    logger = setup_logging()
    count = 0
    
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                try:
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        # Create backup with timestamp
                        backup_path = f"{file_path}.{int(time.time())}.gz"
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(backup_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        # Clear the original file
                        open(file_path, 'w').close()
                        count += 1
                except Exception as e:
                    logger.error(f"Error compressing {file_path}: {e}")
    
    if count > 0:
        logger.info(f"Compressed {count} large log files")

def remove_empty_dirs(log_dir):
    """Remove empty directories."""
    logger = setup_logging()
    count = 0
    
    for root, dirs, files in os.walk(log_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    count += 1
            except Exception as e:
                logger.error(f"Error removing directory {dir_path}: {e}")
    
    if count > 0:
        logger.info(f"Removed {count} empty directories")

def create_backup(log_dir):
    """Create a backup of the logs directory."""
    logger = setup_logging()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"logs_backup_{timestamp}.tar.gz"
    
    try:
        with tarfile.open(backup_name, "w:gz") as tar:
            tar.add(log_dir, arcname=os.path.basename(log_dir))
        logger.info(f"Created backup: {backup_name}")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")

def main():
    parser = argparse.ArgumentParser(description='Log cleanup and rotation script')
    parser.add_argument('--log-dir', default='logs', help='Log directory to clean')
    parser.add_argument('--max-size', type=float, default=10, help='Maximum log file size in MB')
    parser.add_argument('--max-age', type=int, default=7, help='Maximum log age in days')
    parser.add_argument('--clear-empty', action='store_true', help='Remove empty directories')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--interval', type=int, default=3600, help='Check interval in seconds (daemon mode)')
    parser.add_argument('--backup', action='store_true', help='Create backup before cleanup')
    
    args = parser.parse_args()
    logger = setup_logging()
    
    if args.backup:
        create_backup(args.log_dir)
    
    if args.daemon:
        logger.info(f"Starting log cleanup daemon (interval: {args.interval}s)")
        while True:
            try:
                cleanup_old_logs(args.log_dir, args.max_age)
                compress_large_logs(args.log_dir, args.max_size)
                if args.clear_empty:
                    remove_empty_dirs(args.log_dir)
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Log cleanup daemon stopped")
                break
            except Exception as e:
                logger.error(f"Error in daemon mode: {e}")
                time.sleep(60)  # Wait before retrying
    else:
        cleanup_old_logs(args.log_dir, args.max_age)
        compress_large_logs(args.log_dir, args.max_size)
        if args.clear_empty:
            remove_empty_dirs(args.log_dir)

if __name__ == '__main__':
    main()