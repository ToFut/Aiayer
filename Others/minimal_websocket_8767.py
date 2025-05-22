#!/usr/bin/env python3
"""
Minimal WebSocket Server on port 8767
A bare-bones WebSocket server with no external dependencies (except websockets)
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Try to import websockets library
try:
    import websockets
except ImportError:
    print("Installing websockets package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

print(f"Starting minimal WebSocket server on port 8767...")

# Simple WebSocket handler
async def handler(websocket):
    print(f"Client connected!")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to minimal WebSocket server on port 8767",
            "timestamp": str(datetime.now())
        }))
        
        # Process messages
        async for message in websocket:
            print(f"Received: {message}")
            
            # Echo the message back
            try:
                # Try to parse as JSON
                data = json.loads(message)
                await websocket.send(json.dumps({
                    "type": "echo",
                    "data": data,
                    "timestamp": str(datetime.now())
                }))
            except:
                # Fall back to plain text echo
                await websocket.send(f"Echo: {message}")
    
    except Exception as e:
        print(f"Error: {e}")

async def main():
    port = 8767
    host = "localhost"
    
    try:
        # Create pids directory
        os.makedirs("pids", exist_ok=True)
        
        # Save PID
        with open("pids/minimal_ws_8767.pid", "w") as f:
            f.write(str(os.getpid()))
        
        print(f"Starting server on {host}:{port}...")
        
        # Start server
        async with websockets.serve(handler, host, port):
            print(f"Server running at ws://{host}:{port}")
            
            # Run forever
            await asyncio.Future()
            
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

# Main entry point
if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)