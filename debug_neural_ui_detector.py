#!/usr/bin/env python3
"""
Debug script for the Neural UI Detector

This script monitors the logs and tests the server functionality.
"""

import os
import sys
import time
import json
import asyncio
import websockets
import subprocess
from datetime import datetime

# Set up colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_status(text, color=Colors.BLUE):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {text}{Colors.ENDC}")

async def test_websocket(url="ws://localhost:8768"):
    """Test the WebSocket connection and functionality"""
    print_status(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print_status("Connected successfully!", Colors.GREEN)
            
            # Wait for welcome message
            response = await websocket.recv()
            data = json.loads(response)
            print_status(f"Received welcome message: {data.get('message', 'No message')}", Colors.GREEN)
            
            # Send a detect request
            print_status("Sending detect request...", Colors.YELLOW)
            await websocket.send(json.dumps({
                "action": "detect",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for response with timeout
            print_status("Waiting for detection results...", Colors.YELLOW)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                element_count = len(data.get("elements", []))
                print_status(f"Received detection results: {element_count} elements detected!", Colors.GREEN)
                
                # Test specific element detection
                print_status("Testing button detection...", Colors.YELLOW)
                await websocket.send(json.dumps({
                    "action": "find",
                    "description": "button",
                    "element_type": "button",
                    "timestamp": datetime.now().isoformat()
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                if data.get("found", False):
                    print_status(f"Button found: {data.get('element', {}).get('text', 'No text')}", Colors.GREEN)
                else:
                    print_status(f"Button not found: {data.get('message', 'No message')}", Colors.RED)
                
                return True
                
            except asyncio.TimeoutError:
                print_status("Timeout waiting for detection results!", Colors.RED)
                return False
                
    except Exception as e:
        print_status(f"Error connecting to WebSocket: {e}", Colors.RED)
        return False

def monitor_logs(log_file, duration=30):
    """Monitor the log file for the specified duration"""
    print_status(f"Monitoring logs in {log_file} for {duration} seconds...")
    
    # Start tail process
    tail_process = subprocess.Popen(
        ["tail", "-f", log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            line = tail_process.stdout.readline().strip()
            if line:
                # Color code log lines
                if "ERROR" in line:
                    print(f"{Colors.RED}{line}{Colors.ENDC}")
                elif "WARNING" in line:
                    print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
                elif "INFO" in line:
                    print(f"{Colors.BLUE}{line}{Colors.ENDC}")
                else:
                    print(line)
    except KeyboardInterrupt:
        print_status("Log monitoring stopped by user", Colors.YELLOW)
    finally:
        tail_process.terminate()

def check_server_status():
    """Check if the Neural UI Detector server is running"""
    try:
        # Try to find the process
        result = subprocess.run(
            ["lsof", "-i", ":8768"],
            capture_output=True,
            text=True
        )
        
        if "Python" in result.stdout and "LISTEN" in result.stdout:
            print_status("Neural UI Detector server is running on port 8768", Colors.GREEN)
            # Extract PID
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 1:
                    pid = parts[1]
                    print_status(f"Server PID: {pid}", Colors.GREEN)
                    
                    # Check process uptime
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "etime="],
                        capture_output=True,
                        text=True
                    )
                    uptime = ps_result.stdout.strip()
                    print_status(f"Server uptime: {uptime}", Colors.GREEN)
            return True
        else:
            print_status("Neural UI Detector server is NOT running on port 8768", Colors.RED)
            return False
    except Exception as e:
        print_status(f"Error checking server status: {e}", Colors.RED)
        return False

async def main():
    """Main function"""
    print_header("Neural UI Detector Debug Tool")
    
    # Check server status
    server_running = check_server_status()
    
    if server_running:
        # Test WebSocket connection
        await test_websocket()
    
    # Monitor logs
    log_file = os.path.join("logs", "neural_ui_detector", "neural_detector.log")
    if os.path.exists(log_file):
        monitor_logs(log_file)
    else:
        print_status(f"Log file not found: {log_file}", Colors.RED)

if __name__ == "__main__":
    asyncio.run(main())