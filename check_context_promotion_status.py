#!/usr/bin/env python3
"""
Check Context Memory Promotion Status

Display statistics and status information about the context memory promotion process.
"""
import os
import json
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("status")

def main():
    """Display status and statistics for context memory promotion"""
    stats_file = "memory/memory/context_promotion_stats.json"
    pid_file = "memory/context_promotion.pid"
    
    # Check if process is running
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        
        # Check if process with this PID exists
        try:
            os.kill(int(pid), 0)  # Signal 0 doesn't kill the process, just checks if it exists
            process_status = f"✅ RUNNING (PID: {pid})"
        except (OSError, ProcessLookupError):
            process_status = f"❌ NOT RUNNING (stale PID file: {pid})"
    else:
        process_status = "❌ NOT RUNNING (no PID file)"
    
    logger.info("Context Memory Promotion Status:")
    logger.info("-------------------------------")
    logger.info(f"Process Status: {process_status}")
    
    # Check statistics
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            logger.info("\nPromotion Statistics:")
            logger.info("---------------------")
            logger.info(f"Total Runs: {stats.get('total_runs', 0)}")
            logger.info(f"Total Promoted Items: {stats.get('promoted_items', 0)}")
            
            # Format last run time
            last_run = stats.get('last_run')
            if last_run:
                try:
                    last_run_time = datetime.fromisoformat(last_run)
                    time_diff = datetime.now() - last_run_time
                    if time_diff.total_seconds() < 60:
                        time_ago = f"{int(time_diff.total_seconds())} seconds ago"
                    elif time_diff.total_seconds() < 3600:
                        time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
                    else:
                        time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
                    
                    logger.info(f"Last Run: {last_run} ({time_ago})")
                except (ValueError, TypeError):
                    logger.info(f"Last Run: {last_run}")
            else:
                logger.info("Last Run: Never")
            
        except (json.JSONDecodeError, IOError) as e:
            logger.info(f"\nError reading statistics file: {e}")
    else:
        logger.info("\nNo statistics file found. The promotion process may not have run yet.")
    
    # Check log file
    log_file = "logs/memory/context_promotion.log"
    if os.path.exists(log_file):
        try:
            # Get the last 5 log entries
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
            
            if log_lines:
                logger.info("\nRecent Log Entries:")
                logger.info("------------------")
                for line in log_lines[-5:]:
                    logger.info(line.strip())
        except IOError as e:
            logger.info(f"\nError reading log file: {e}")
    else:
        logger.info("\nNo log file found.")

if __name__ == "__main__":
    main()