#!/usr/bin/env python3
"""
Enhanced WebSocket server for port 8765 with proper agent_confirmation handling and verbose debugging
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import time

# Configure logging with more detail
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_ws_8765.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('enhanced_ws_8765')
logger.setLevel(logging.DEBUG)

# Track connected clients with detailed info
connected_clients = {}

# Handler for WebSocket connections (current websockets API)
async def handler(websocket):
    """WebSocket connection handler with enhanced logging"""
    client_id = f"client_{id(websocket)}"
    start_time = datetime.now()
    remote_address = "unknown"
    
    try:
        remote_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    except:
        pass
    
    # Track connection details
    connected_clients[client_id] = {
        "websocket": websocket,
        "connected_at": start_time,
        "remote_address": remote_address,
        "messages_received": 0,
        "messages_sent": 0,
        "last_activity": start_time
    }
    
    logger.info(f"🟢 Client {client_id} connected from {remote_address}")
    print(f"🟢 Client connected from {remote_address}")
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "welcome",
            "message": f"Connected to enhanced WebSocket server on port 8765",
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "version": "1.0.0",
                "capabilities": ["agent_confirmation", "progress_tracking", "execution_success"]
            }
        }
        await websocket.send(json.dumps(welcome_msg))
        connected_clients[client_id]["messages_sent"] += 1
        logger.info(f"📤 Sent welcome message to {client_id}")
        
        # Handle incoming messages
        async for message in websocket:
            connected_clients[client_id]["last_activity"] = datetime.now()
            connected_clients[client_id]["messages_received"] += 1
            
            # Log raw message first
            logger.debug(f"📥 Raw message from {client_id}: {message}")
            print(f"📥 Raw message: {message[:100]}...")
            
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"📦 Message type from {client_id}: {msg_type}")
                print(f"📦 Message type: {msg_type}")
                
                # Handle agent_confirmation message (DO button)
                if msg_type == 'agent_confirmation':
                    session_id = data.get('session_id', '')
                    action = data.get('action', '').upper()
                    
                    logger.info(f"🎯 Agent confirmation received from {client_id}: action={action}, session_id={session_id}")
                    print(f"🎯 Agent confirmation: action={action}, session_id={session_id}")
                    
                    if action == 'DO':
                        # Send immediate progress update
                        progress_msg = {
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 1,
                            "progress": 20,
                            "message": "🚀 Starting execution: Analyzing screen..."
                        }
                        await websocket.send(json.dumps(progress_msg))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent progress update (20%) to {client_id}")
                        print(f"📤 Sent progress update (20%)")
                        
                        # Simulate some processing time
                        await asyncio.sleep(1)
                        
                        # Send another progress update
                        progress_msg = {
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 2,
                            "progress": 50,
                            "message": "🔎 Locating UI elements..."
                        }
                        await websocket.send(json.dumps(progress_msg))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent progress update (50%) to {client_id}")
                        print(f"📤 Sent progress update (50%)")
                        
                        await asyncio.sleep(1)
                        
                        # Send third progress update
                        progress_msg = {
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 3,
                            "progress": 80,
                            "message": "⚡ Executing automation steps..."
                        }
                        await websocket.send(json.dumps(progress_msg))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent progress update (80%) to {client_id}")
                        print(f"📤 Sent progress update (80%)")
                        
                        await asyncio.sleep(1)
                        
                        # Send completion message
                        success_msg = {
                            "type": "agent_execution_success",
                            "session_id": session_id,
                            "result": {
                                "success": True,
                                "steps_executed": 3,
                                "execution_time": 3.0
                            },
                            "summary": "Task completed successfully! All steps were executed as planned.",
                            "execution_completed": True
                        }
                        await websocket.send(json.dumps(success_msg))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent execution success to {client_id}")
                        print(f"📤 Sent execution success")
                        
                    elif action == 'DISMISS':
                        # Send dismissed message
                        await websocket.send(json.dumps({
                            "type": "agent_dismissed",
                            "session_id": session_id,
                            "message": "Plan dismissed by user"
                        }))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent dismiss confirmation to {client_id}")
                        
                    elif action == 'ADJUST':
                        # Send adjustment request message
                        await websocket.send(json.dumps({
                            "type": "agent_adjustment_request",
                            "session_id": session_id,
                            "message": "Please provide more details about what you'd like to adjust."
                        }))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.info(f"📤 Sent adjust confirmation to {client_id}")
                        
                    else:
                        # Send error for unknown action
                        await websocket.send(json.dumps({
                            "type": "agent_confirmation_error",
                            "error": f"Unknown action: {action}",
                            "session_id": session_id
                        }))
                        connected_clients[client_id]["messages_sent"] += 1
                        logger.warning(f"📤 Sent error for unknown action to {client_id}: {action}")
                
                # Handle ping messages
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    connected_clients[client_id]["messages_sent"] += 1
                    logger.debug(f"📤 Sent pong to {client_id}")
                
                # Handle other message types
                else:
                    # Send a default response
                    response = {
                        "type": "response",
                        "original_type": msg_type,
                        "payload": {
                            "message": f"Received {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                    connected_clients[client_id]["messages_sent"] += 1
                    logger.info(f"📤 Sent default response to {client_id} for type {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
                connected_clients[client_id]["messages_sent"] += 1
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"🔴 Connection closed with {client_id}: {e}")
        print(f"🔴 Connection closed: {e}")
    except Exception as e:
        logger.error(f"❌ Error handling client {client_id}: {e}")
        print(f"❌ Error handling client: {e}")
    finally:
        if client_id in connected_clients:
            del connected_clients[client_id]
        logger.info(f"🔴 Client {client_id} disconnected after {(datetime.now() - start_time).total_seconds():.2f}s")
        print(f"🔴 Client disconnected")

async def status_reporter():
    """Periodically report connection status"""
    while True:
        try:
            total_clients = len(connected_clients)
            if total_clients > 0:
                logger.info(f"🔍 Status: {total_clients} client(s) connected")
                
                for client_id, info in connected_clients.items():
                    uptime = (datetime.now() - info["connected_at"]).total_seconds()
                    last_activity = (datetime.now() - info["last_activity"]).total_seconds()
                    logger.info(f"   - {client_id} from {info['remote_address']}: "
                                f"up {uptime:.2f}s, "
                                f"last activity {last_activity:.2f}s ago, "
                                f"msgs in/out: {info['messages_received']}/{info['messages_sent']}")
            
            await asyncio.sleep(30)  # Report every 30 seconds
        except Exception as e:
            logger.error(f"Error in status reporter: {e}")
            await asyncio.sleep(60)  # Wait longer on error

async def main():
    # Ensure port 8765 is available
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', 8765))
        test_socket.close()
        logger.info("✅ Port 8765 is available")
    except OSError:
        logger.error("❌ Port 8765 is already in use. Please stop any existing WebSocket servers.")
        print("❌ Port 8765 is already in use. Stopping...")
        
        # Try to kill any processes using the port
        try:
            import subprocess
            subprocess.run("lsof -ti:8765 | xargs kill -9 2>/dev/null || true", shell=True)
            logger.info("🔥 Killed existing processes using port 8765")
            print("🔥 Killed existing processes using port 8765")
            
            # Wait for port to become available
            for _ in range(3):
                await asyncio.sleep(1)
                try:
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.bind(('localhost', 8765))
                    test_socket.close()
                    logger.info("✅ Port 8765 is now available")
                    break
                except OSError:
                    pass
            else:
                logger.error("❌ Failed to free up port 8765 after multiple attempts")
                print("❌ Failed to free up port 8765. Please check manually.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error while trying to free port: {e}")
            print(f"❌ Error while trying to free port: {e}")
            sys.exit(1)
    
    # Start WebSocket server
    port = 8765
    host = "localhost"
    
    logger.info(f"🚀 Starting enhanced WebSocket server on {host}:{port}")
    print(f"🚀 Starting enhanced WebSocket server on {host}:{port}")
    
    # Start status reporter
    status_task = asyncio.create_task(status_reporter())
    
    # Serve WebSocket
    server = await websockets.serve(
        handler,
        host,
        port,
        ping_interval=30,
        ping_timeout=60,
        close_timeout=30,
        max_size=10 * 1024 * 1024,
        max_queue=32
    )
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/enhanced_ws_8765.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"✅ Enhanced WebSocket server running on ws://{host}:{port}")
    print(f"✅ Enhanced WebSocket server running on ws://{host}:{port}")
    logger.info(f"🎯 Ready to handle agent_confirmation messages with verbose logging")
    print(f"🎯 Ready to handle agent_confirmation messages with verbose logging")
    
    # Keep running indefinitely
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}")
        print(f"❌ Error starting server: {e}")
        sys.exit(1)