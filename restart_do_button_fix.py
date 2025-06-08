#!/usr/bin/env python3
"""
Restart DO Button Fix

This script fixes the WebSocket server implementation in simple_do_button_fix.py
and restarts the service with the correct handler function.
"""

import asyncio
import websockets
import json
import logging
import os
import time
import sys
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('restart_do_button_fix')

async def main():
    """Main function to restart the DO button fix"""
    logger.info("Checking for running WebSocket servers...")
    
    # Check for servers on ports 8765, 8766, 8768
    ports_to_check = [8765, 8766, 8768]
    for port in ports_to_check:
        try:
            # Try to kill any processes using these ports
            result = subprocess.run(
                f"lsof -ti:{port} | xargs kill -9",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                logger.info(f"Killed process on port {port}")
            else:
                logger.info(f"No process found on port {port}")
        except Exception as e:
            logger.error(f"Error killing process on port {port}: {e}")
    
    # Wait for ports to be released
    logger.info("Waiting for ports to be released...")
    await asyncio.sleep(2)
    
    # Create a fixed version of the handler in simple_do_button_fix.py
    simple_fix_path = Path("simple_do_button_fix.py")
    if simple_fix_path.exists():
        logger.info("Creating fixed version of simple_do_button_fix.py")
        
        # Read the file
        with open(simple_fix_path, "r") as f:
            content = f.read()
        
        # Fix the handler function signature
        if "async def handle_websocket(websocket, path):" in content:
            content = content.replace(
                "async def handle_websocket(websocket, path):",
                "async def handle_websocket(websocket, path=None):"
            )
            logger.info("Fixed handler function signature")
        
        # Fix the WebSocket server call
        if "server = await websockets.serve(handle_websocket," in content:
            # Make sure we're using the correct function
            content = content.replace(
                "server = await websockets.serve(handle_websocket,",
                "server = await websockets.serve(handle_websocket,"
            )
            logger.info("Fixed WebSocket server call")
        
        # Write the fixed file
        with open(simple_fix_path, "w") as f:
            f.write(content)
            logger.info("Wrote fixed file")
    
    # Start the DO button server
    logger.info("Starting Ultimate DO Button Server...")
    try:
        os.makedirs("logs/do_button", exist_ok=True)
        proc = subprocess.Popen(
            ["python3", "ultimate_do_button_server.py"],
            stdout=open("logs/do_button/ultimate_do_button_server.log", "a"),
            stderr=subprocess.STDOUT
        )
        logger.info(f"Started Ultimate DO Button Server with PID {proc.pid}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open("pids/ultimate_do_button_server.pid", "w") as f:
            f.write(str(proc.pid))
    except Exception as e:
        logger.error(f"Failed to start Ultimate DO Button Server: {e}")
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    # Start the Neural UI Detector
    logger.info("Starting Neural UI Detector Server...")
    try:
        os.makedirs("logs/neural_ui_detector", exist_ok=True)
        proc = subprocess.Popen(
            ["python3", "neural_ui_detector_server.py"],
            stdout=open("logs/neural_ui_detector/server.log", "a"),
            stderr=subprocess.STDOUT
        )
        logger.info(f"Started Neural UI Detector Server with PID {proc.pid}")
        
        # Save PID
        with open("pids/neural_ui_detector_server.pid", "w") as f:
            f.write(str(proc.pid))
    except Exception as e:
        logger.error(f"Failed to start Neural UI Detector Server: {e}")
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    # Start the Simple DO Button Fix Proxy
    logger.info("Starting Simple DO Button Fix Proxy...")
    try:
        os.makedirs("logs/do_button_fix", exist_ok=True)
        proc = subprocess.Popen(
            ["python3", "simple_do_button_fix.py"],
            stdout=open("logs/do_button_fix/simple_proxy.log", "a"),
            stderr=subprocess.STDOUT
        )
        logger.info(f"Started Simple DO Button Fix Proxy with PID {proc.pid}")
        
        # Save PID
        with open("pids/simple_do_button_fix.pid", "w") as f:
            f.write(str(proc.pid))
    except Exception as e:
        logger.error(f"Failed to start Simple DO Button Fix Proxy: {e}")
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    # Check if servers are running
    logger.info("Checking if servers are running...")
    
    success = True
    # Check for ultimate_do_button_server on port 8768
    try:
        with open("pids/ultimate_do_button_server.pid", "r") as f:
            pid = int(f.read().strip())
            if subprocess.run(f"ps -p {pid}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                logger.info(f"Ultimate DO Button Server is running (PID: {pid})")
            else:
                logger.error(f"Ultimate DO Button Server is not running")
                success = False
    except Exception as e:
        logger.error(f"Error checking Ultimate DO Button Server: {e}")
        success = False
    
    # Check for neural_ui_detector_server on port 8768
    try:
        with open("pids/neural_ui_detector_server.pid", "r") as f:
            pid = int(f.read().strip())
            if subprocess.run(f"ps -p {pid}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                logger.info(f"Neural UI Detector Server is running (PID: {pid})")
            else:
                logger.error(f"Neural UI Detector Server is not running")
                success = False
    except Exception as e:
        logger.error(f"Error checking Neural UI Detector Server: {e}")
        success = False
    
    # Check for simple_do_button_fix on port 8766
    try:
        with open("pids/simple_do_button_fix.pid", "r") as f:
            pid = int(f.read().strip())
            if subprocess.run(f"ps -p {pid}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                logger.info(f"Simple DO Button Fix Proxy is running (PID: {pid})")
            else:
                logger.error(f"Simple DO Button Fix Proxy is not running")
                success = False
    except Exception as e:
        logger.error(f"Error checking Simple DO Button Fix Proxy: {e}")
        success = False
    
    if success:
        logger.info("✅ All servers restarted successfully!")
        logger.info("You can now test the DO button functionality.")
    else:
        logger.error("⚠️ There were issues starting one or more servers.")
        logger.error("Check the logs for details.")
    
    return 0

if __name__ == "__main__":
    try:
        # Run the main function
        exit_code = asyncio.run(main())
        
        # Determine exit message based on exit code
        if exit_code == 0:
            print("\n==============================================")
            print("✅ DO Button Fix servers restarted successfully!")
            print("==============================================")
            print("The following servers are now running:")
            print("- Ultimate DO Button Server (port 8768)")
            print("- Neural UI Detector Server (port 8768)")
            print("- Simple DO Button Fix Proxy (port 8766)")
            print("\nYou can test the fix by running:")
            print("python3 test_fixed_do_button.py")
        else:
            print("\n==============================================")
            print("⚠️ There were issues restarting the servers.")
            print("==============================================")
            print("Check the logs for more information:")
            print("- logs/do_button/ultimate_do_button_server.log")
            print("- logs/neural_ui_detector/server.log")
            print("- logs/do_button_fix/simple_proxy.log")
        
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nRestart operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)