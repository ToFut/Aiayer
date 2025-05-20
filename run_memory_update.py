#!/usr/bin/env python3
"""
Runner script to periodically update the conscious memory by integrating sensor data
This script runs the update_conscious.py file at regular intervals and 
maintains the integration of screen, process, and file sensor data
"""
import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory_runner.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory.runner")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Conscious Memory Update Runner')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Interval in seconds between updates (default: 30)')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    return parser.parse_args()

def setup():
    """Setup environment for running the update script"""
    # Create log directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Get path to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    memory_dir = os.path.join(script_dir, "memory")
    update_script_path = os.path.join(memory_dir, "update_conscious.py")
    
    # Check if update script exists
    if not os.path.exists(update_script_path):
        logger.error(f"Update script not found at {update_script_path}")
        sys.exit(1)
    
    return update_script_path

def run_update(script_path, verbose=False):
    """Run the update conscious script"""
    try:
        logger.info(f"Running update script at {script_path}")
        start_time = time.time()
        
        # Run the script as a subprocess
        if verbose:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
        else:
            result = subprocess.run(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logger.info(f"Successfully updated conscious memory in {duration:.2f} seconds")
            return True
        else:
            logger.error(f"Failed to update conscious memory: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running update script: {e}")
        return False

def main():
    """Main function to run the memory update process"""
    args = parse_arguments()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Setup environment
    update_script_path = setup()
    
    # Get the update interval
    update_interval = args.interval
    
    logger.info(f"Starting conscious memory updater with {update_interval}s interval")
    logger.info(f"Press Ctrl+C to stop the runner")
    
    try:
        while True:
            run_update(update_script_path, args.verbose)
            logger.info(f"Waiting {update_interval} seconds until next update...")
            time.sleep(update_interval)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Memory updater stopped")

if __name__ == "__main__":
    main()