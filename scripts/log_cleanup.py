#!/usr/bin/env python3
"""
Log Cleanup Utility

This script handles log rotation, compression, and cleanup to manage log sizes.
It can be run as a scheduled task to keep log sizes under control.
"""

import os
import shutil
import gzip
import time
import datetime
import argparse
import glob
from pathlib import Path

def compress_file(file_path, delete_original=True):
    """Compress a file using gzip and optionally delete the original."""
    compressed_path = f"{file_path}.gz"
    try:
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        if delete_original:
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error compressing {file_path}: {e}")
        return False

def rotate_logs(log_dir, max_size_mb=50, max_age_days=7, archive_dir=None):
    """
    Rotate log files that exceed max_size_mb or are older than max_age_days.
    Archive functionality is disabled.
    
    Args:
        log_dir: Directory containing log files
        max_size_mb: Maximum size in MB before rotation (default: 50MB)
        max_age_days: Maximum age in days before rotation (default: 7 days)
        archive_dir: Not used - archive functionality is disabled
    """
    if not os.path.exists(log_dir):
        print(f"Log directory {log_dir} does not exist.")
        return
    
    # Get current time
    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Find all log files
    log_files = []
    for ext in ['.log', '.out']:
        log_files.extend(glob.glob(os.path.join(log_dir, f"**/*{ext}"), recursive=True))
    
    rotated_count = 0
    
    for log_file in log_files:
        # Skip directories and already compressed files
        if os.path.isdir(log_file) or '.gz' in log_file:
            continue
        
        try:
            file_stat = os.stat(log_file)
            file_age = now - file_stat.st_mtime
            file_size = file_stat.st_size
            
            # Special handling for backend logs
            if 'backend' in log_file:
                max_size_bytes = 1 * 1024 * 1024  # 1MB for backend logs
                max_age_seconds = 24 * 60 * 60  # 1 day for backend logs
            
            # Determine if the file should be rotated
            should_rotate = False
            reason = ""
            
            if file_size > max_size_bytes:
                should_rotate = True
                reason = f"size ({file_size / 1024 / 1024:.2f}MB > {max_size_mb}MB)"
            
            if file_age > max_age_seconds:
                should_rotate = True
                age_days = file_age / 86400
                reason = f"age ({age_days:.1f} days > {max_age_days} days)"
            
            if should_rotate:
                # Clear the original file
                with open(log_file, 'w') as f:
                    f.write(f"Log rotated at {datetime.datetime.now()} due to {reason}\n")
                
                rotated_count += 1
                print(f"Rotated {log_file} due to {reason}")
        
        except Exception as e:
            print(f"Error processing {log_file}: {e}")
    
    print(f"Rotation complete: {rotated_count} files rotated")

def cleanup_archives(archive_dir, max_age_days=30):
    """Archive cleanup is disabled."""
    print("Archive cleanup is disabled")
    return

def clear_empty_logs(log_dir, exclude_patterns=None):
    """Clear logs that contain only empty data records to save space."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    empty_patterns = [
        'memory_state_saving_long_term: []',
        'memory_state_snapshot_long_term: []'
    ]
    
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True):
        # Skip excluded patterns
        if any(pattern in log_file for pattern in exclude_patterns):
            continue
            
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Check if file contains only empty memory state logs
            is_only_empty = True
            for line in content.split('\n'):
                if line.strip() and not any(pattern in line for pattern in empty_patterns):
                    is_only_empty = False
                    break
            
            # Clear the file if it only has empty state logs
            if is_only_empty and content.strip():
                with open(log_file, 'w') as f:
                    f.write(f"Empty logs cleared at {datetime.datetime.now()}\n")
                print(f"Cleared empty log file: {log_file}")
        except Exception as e:
            print(f"Error processing {log_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log rotation and cleanup utility")
    parser.add_argument("--log-dir", default="logs", help="Directory containing log files")
    parser.add_argument("--archive-dir", help="Directory to store archived logs")
    parser.add_argument("--max-size", type=int, default=50, help="Maximum log size in MB before rotation")
    parser.add_argument("--max-age", type=int, default=7, help="Maximum log age in days before rotation")
    parser.add_argument("--clear-empty", action="store_true", help="Clear logs that contain only empty data")
    
    args = parser.parse_args()
    
    # Get absolute paths
    log_dir = os.path.abspath(args.log_dir)
    archive_dir = args.archive_dir
    if archive_dir:
        archive_dir = os.path.abspath(archive_dir)
    
    print(f"Processing logs in {log_dir}")
    rotate_logs(log_dir, args.max_size, args.max_age, archive_dir)
    
    if args.clear_empty:
        print("Clearing empty logs...")
        clear_empty_logs(log_dir)