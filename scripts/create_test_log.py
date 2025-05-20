#!/usr/bin/env python3
"""
Create a test log file for testing the log monitor.
This script creates a large log file of the specified size.
"""

import os
import sys
import argparse
import random
from datetime import datetime

# Sample log lines
LOG_SAMPLES = [
    "INFO: User action completed successfully",
    "DEBUG: Processing request from user",
    "ERROR: Failed to connect to database",
    "WARNING: Memory usage is high",
    "INFO: Screen sensor captured new data",
    "DEBUG: Websocket message received",
    "INFO: File system event detected",
    "WARNING: API request rate limit approaching",
    "ERROR: Could not parse JSON data",
    "DEBUG: Memory serialization completed",
    "INFO: Bridge server forwarded message"
]

def create_large_log(output_path, size_mb):
    """Create a log file of specified size in MB."""
    # Calculate approximate bytes per line (average log line length + newline)
    avg_bytes_per_line = sum(len(line) for line in LOG_SAMPLES) / len(LOG_SAMPLES) + 1
    
    # Calculate number of lines needed
    target_bytes = size_mb * 1024 * 1024
    estimated_lines = int(target_bytes / avg_bytes_per_line)
    
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        bytes_written = 0
        lines_written = 0
        
        while bytes_written < target_bytes:
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_line = random.choice(LOG_SAMPLES)
            full_line = f"{timestamp} - {log_line}\n"
            
            f.write(full_line)
            bytes_written += len(full_line)
            lines_written += 1
            
            # Print progress every 100,000 lines
            if lines_written % 100000 == 0:
                mb_written = bytes_written / (1024 * 1024)
                print(f"Written {lines_written:,} lines ({mb_written:.2f} MB / {size_mb:.2f} MB)")
    
    # Final stats
    mb_written = bytes_written / (1024 * 1024)
    print(f"Finished creating log file:")
    print(f"- Path: {output_path}")
    print(f"- Size: {mb_written:.2f} MB")
    print(f"- Lines: {lines_written:,}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a large log file for testing")
    parser.add_argument("--size", type=float, default=550, help="Size in MB (default: 550)")
    parser.add_argument("--output", type=str, default="../logs/test_large_log.log", 
                        help="Output file path (default: ../logs/test_large_log.log)")
    
    args = parser.parse_args()
    
    # Normalize the path
    output_path = os.path.abspath(args.output)
    
    print(f"Creating test log file of {args.size} MB at {output_path}")
    create_large_log(output_path, args.size)