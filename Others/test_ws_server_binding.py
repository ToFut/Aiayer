#!/usr/bin/env python3
"""
Test WebSocket Server Binding
Tests binding WebSocket server to different addresses to troubleshoot connection issues
"""
import asyncio
import websockets
import logging
import os
import sys
import socket
import signal
import json
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_ws_binding.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_ws_binding')

# Global variables
running = True

def is_port_in_use(port, host='localhost'):
    """Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if host == 'localhost':
                host = '127.0.0.1'
            return s.connect_ex((host, port)) == 0
    except Exception as e:
        logger.error(f"Error checking port: {e}")
        return False

async def handler(websocket):
    """Handle WebSocket connections."""
    client_id = id(websocket)
    client_info = websocket.remote_address if hasattr(websocket, 'remote_address') else "Unknown"
    logger.info(f"Client {client_id} connected from {client_info}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}!",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Echo back the message
                response = {
                    "type": "response",
                    "payload": {
                        "message": f"Received {data.get('type', 'unknown')} message",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        logger.info(f"Client {client_id} disconnected")

def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    global running
    logger.info("Received exit signal, shutting down...")
    running = False

async def main():
    """Main function"""
    global running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Port to use
    port = 8765
    
    # First, check if the port is already in use
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use. Server may not start properly.")
    
    # Try binding to different addresses
    binding_configs = [
        {"host": "localhost", "name": "localhost"},
        {"host": "127.0.0.1", "name": "127.0.0.1"},
        {"host": "0.0.0.0", "name": "all interfaces"}
    ]
    
    for config in binding_configs:
        if not running:
            break
            
        host = config["host"]
        name = config["name"]
        
        try:
            logger.info(f"Starting server bound to {name} ({host}) on port {port}")
            
            stop = asyncio.Future()
            server = await websockets.serve(handler, host, port)
            
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            logger.info(f"Server sockets: {server.sockets}")
            
            print(f"\n=== Testing Configuration ===")
            print(f"Host: {host} ({name})")
            print(f"Port: {port}")
            print(f"Server should now be running\n")
            print(f"Test connection with: python -c 'import asyncio, websockets; asyncio.run(websockets.connect(\"ws://{host}:{port}\"))'")
            print(f"Press Ctrl+C to try next configuration or exit\n")
            
            # Wait for stop signal
            try:
                await stop
            except asyncio.CancelledError:
                pass
            finally:
                server.close()
                await server.wait_closed()
                logger.info(f"Server bound to {name} stopped")
                
        except OSError as e:
            logger.error(f"Failed to bind WebSocket server to {name} ({host}): {e}")
        except Exception as e:
            logger.error(f"Error starting server on {name} ({host}): {e}")
        
        print("\nWaiting 5 seconds before trying next configuration...")
        await asyncio.sleep(5)
    
    logger.info("All binding configurations tested")

if __name__ == "__main__":
    print("\n=== WebSocket Server Binding Test ===")
    print("Testing binding to different network interfaces")
    print("This will help diagnose connection issues")
    print("\nPress Ctrl+C to stop each test and move to the next configuration")
    print("=====================================\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")