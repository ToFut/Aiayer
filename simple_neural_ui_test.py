#!/usr/bin/env python3
"""
Simple Neural UI Detector Test Script
This script provides a simple way to test the Neural UI Detector
"""

import asyncio
import json
import subprocess
import os
import sys
import time
import signal
import websockets

# Configuration
PORT = 8769
TEST_DURATION = 60  # seconds

# Ensure the port file exists
def create_port_file():
    try:
        with open("neural_ui_detector_port.txt", "w") as f:
            f.write(str(PORT))
        print(f"Created port file with port {PORT}")
    except Exception as e:
        print(f"Error creating port file: {e}")

# Kill any existing processes on the port
def kill_port_process():
    try:
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            result = subprocess.run(['lsof', f'-ti:{PORT}'], capture_output=True, text=True)
            pids = result.stdout.strip().split('\n')
            
            for pid in pids:
                if pid and pid.strip():
                    try:
                        pid_int = int(pid.strip())
                        os.kill(pid_int, signal.SIGKILL)
                        print(f"Killed process {pid_int} on port {PORT}")
                    except (ValueError, ProcessLookupError) as e:
                        print(f"Failed to kill process {pid}: {e}")
    except Exception as e:
        print(f"Error killing port process: {e}")

# Start the Neural UI Detector server
def start_server():
    try:
        # Prepare command
        cmd = [sys.executable, "fixed_neural_ui_detector_server.py", "--port", str(PORT), "--debug"]
        
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Started Neural UI Detector server with PID {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

# Test WebSocket connection
async def test_websocket():
    url = f"ws://localhost:{PORT}"
    print(f"Testing WebSocket connection to {url}")
    
    try:
        # Connect to server
        async with websockets.connect(url) as ws:
            print("Connected to WebSocket server")
            
            # Receive welcome message
            welcome = await ws.recv()
            try:
                welcome_data = json.loads(welcome)
                print(f"Received welcome message: {welcome_data}")
            except json.JSONDecodeError:
                print(f"Received invalid welcome message: {welcome}")
            
            # Send a test message
            test_message = {
                "type": "test",
                "message": "Hello from test script",
                "timestamp": time.time()
            }
            await ws.send(json.dumps(test_message))
            print(f"Sent test message: {test_message}")
            
            # Receive response
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            try:
                response_data = json.loads(response)
                print(f"Received response: {response_data}")
            except json.JSONDecodeError:
                print(f"Received invalid response: {response}")
            
            # Send detection request
            detect_message = {
                "action": "detect",
                "timestamp": time.time()
            }
            await ws.send(json.dumps(detect_message))
            print(f"Sent detection request: {detect_message}")
            
            # Wait for detection result (with longer timeout)
            try:
                detection_response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                try:
                    detection_data = json.loads(detection_response)
                    print(f"Received detection result: {json.dumps(detection_data, indent=2)}")
                    return True
                except json.JSONDecodeError:
                    print(f"Received invalid detection result: {detection_response}")
            except asyncio.TimeoutError:
                print("Detection request timed out")
            
            return False
    except Exception as e:
        print(f"WebSocket error: {e}")
        return False

# Main function
async def main():
    # Create port file
    create_port_file()
    
    # Kill any existing processes on the port
    kill_port_process()
    
    # Start the server
    server_process = start_server()
    if not server_process:
        print("Failed to start server")
        return 1
    
    print(f"Waiting for server to start (10 seconds)...")
    await asyncio.sleep(10)
    
    # Test WebSocket connection
    success = False
    for i in range(3):  # Try 3 times
        print(f"WebSocket test attempt {i+1}/3")
        success = await test_websocket()
        if success:
            print("✅ WebSocket test successful!")
            break
        print(f"WebSocket test attempt {i+1} failed, retrying in 5 seconds...")
        await asyncio.sleep(5)
    
    if not success:
        print("❌ All WebSocket test attempts failed")
    
    # Keep server running for TEST_DURATION seconds
    print(f"Keeping server running for {TEST_DURATION} seconds...")
    for i in range(TEST_DURATION):
        if i % 10 == 0:
            print(f"{TEST_DURATION - i} seconds remaining...")
        await asyncio.sleep(1)
    
    # Clean up
    print("Test complete, cleaning up...")
    try:
        server_process.terminate()
        await asyncio.sleep(1)
        if server_process.poll() is None:
            server_process.kill()
    except Exception as e:
        print(f"Error terminating server: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)