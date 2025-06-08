#!/usr/bin/env python3
"""
Debug WebSocket connections to see what ports are being used and what traffic is happening
"""
import asyncio
import websockets
import json
import logging
import sys
import os
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_ws_connections.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debug_ws_connections')

# Port to monitor
WS_PORT = 8765
if len(sys.argv) > 1:
    try:
        WS_PORT = int(sys.argv[1])
    except ValueError:
        logger.error(f"Invalid port number: {sys.argv[1]}")
        sys.exit(1)

# Track connected clients
connected_clients = set()

# Debug handler for WebSocket connections
async def debug_handler(websocket):
    """Debug WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    
    # Get client IP and port
    try:
        remote_address = websocket.remote_address
        logger.info(f"🟢 Client {client_id} connected from {remote_address}")
        print(f"🟢 Client connected from {remote_address}")
    except Exception as e:
        logger.error(f"Could not get remote address: {e}")
        print(f"🟢 Client connected (unknown address)")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Debug WebSocket Server - Port {WS_PORT}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                # Log raw message
                logger.info(f"📥 Raw message: {message}")
                print(f"📥 Raw message: {message[:100]}...")
                
                # Try to parse as JSON
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"📦 Message type: {msg_type}")
                    print(f"📦 Message type: {msg_type}")
                    
                    if msg_type == 'agent_confirmation':
                        action = data.get('action', '')
                        session_id = data.get('session_id', '')
                        logger.info(f"🎯 Agent confirmation: action={action}, session_id={session_id}")
                        print(f"🎯 Agent confirmation: action={action}, session_id={session_id}")
                        
                        # Send immediate progress update
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 1,
                            "progress": 20,
                            "message": "🚀 DEBUG: Starting execution: Analyzing screen..."
                        }))
                        
                        await asyncio.sleep(1)
                        
                        # Send second progress update
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 2,
                            "progress": 50,
                            "message": "🔎 DEBUG: Locating UI elements..."
                        }))
                        
                        await asyncio.sleep(1)
                        
                        # Send third progress update
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 3,
                            "progress": 80,
                            "message": "⚡ DEBUG: Executing automation steps..."
                        }))
                        
                        await asyncio.sleep(1)
                        
                        # Send completion message
                        await websocket.send(json.dumps({
                            "type": "agent_execution_success",
                            "session_id": session_id,
                            "result": {
                                "success": True,
                                "steps_executed": 3,
                                "execution_time": 3.0
                            },
                            "summary": "DEBUG: Task completed successfully! This is a debug message to verify DO button functionality.",
                            "execution_completed": True
                        }))
                        
                        logger.info(f"✅ Sent debug execution success for {session_id}")
                        print(f"✅ Sent debug execution success for {session_id}")
                    
                    # Echo all other messages
                    else:
                        await websocket.send(json.dumps({
                            "type": "debug_echo",
                            "original_type": msg_type,
                            "timestamp": datetime.now().isoformat(),
                            "message": "This is a debug echo response"
                        }))
                
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON message: {message[:100]}...")
                    print(f"⚠️ Non-JSON message received")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                print(f"❌ Error handling message: {e}")
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
        print(f"🔴 Connection closed: {e}")
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        print(f"❌ Error in handler: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")
        print(f"🔴 Client disconnected")

async def main():
    # Kill any existing process on the port
    try:
        import subprocess
        subprocess.run(f"lsof -ti:{WS_PORT} | xargs kill -9", shell=True)
        logger.info(f"Killed any existing process on port {WS_PORT}")
    except Exception as e:
        logger.error(f"Error killing existing process: {e}")
    
    # Start WebSocket server
    host = "localhost"
    
    try:
        logger.info(f"Starting debug WebSocket server on {host}:{WS_PORT}")
        print(f"🚀 Starting debug WebSocket server on {host}:{WS_PORT}")
        
        server = await websockets.serve(
            debug_handler,
            host,
            WS_PORT,
            ping_interval=30,
            ping_timeout=60,
            close_timeout=30,
            max_size=10 * 1024 * 1024,
            max_queue=32
        )
        
        logger.info(f"Debug WebSocket server running on ws://{host}:{WS_PORT}")
        print(f"✅ Debug WebSocket server running on ws://{host}:{WS_PORT}")
        print(f"📝 Logging to logs/debug_ws_connections.log")
        
        # Keep running
        await asyncio.Future()
    
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)