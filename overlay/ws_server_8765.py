#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ws_server_8765')

# Track connected clients
connected_clients = set()
llm_websocket = None
llm_lock = asyncio.Lock()  # Add lock for LLM WebSocket operations

async def connect_to_llm():
    """Connect to the LLM service"""
    global llm_websocket
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if llm_websocket:
                try:
                    await llm_websocket.close()
                except:
                    pass
                llm_websocket = None
                
            logger.info("Connecting to LLM service...")
            llm_websocket = await websockets.connect(
                'ws://localhost:8770',
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=60,   # Wait 60 seconds for pong
                close_timeout=30,  # Wait 30 seconds for clean closure
                max_size=10 * 1024 * 1024,  # 10MB max message size
                max_queue=32,      # Max message queue size
                compression=None   # Disable compression
            )
            logger.info("Connected to LLM service")
            return True
        except Exception as e:
            retry_count += 1
            logger.error(f"Failed to connect to LLM service (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            else:
                logger.error("Max retries reached for LLM service connection")
                return False

async def forward_to_llm(message):
    """Forward a message to the LLM service"""
    global llm_websocket
    max_retries = 3  # Increased retries
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if not llm_websocket or not llm_websocket.open:
                logger.info("Attempting to connect to LLM service...")
                if not await connect_to_llm():
                    logger.error("Failed to connect to LLM service after retries")
                    return None
            
            # Send message with timeout
            try:
                logger.info("Sending message to LLM service...")
                await asyncio.wait_for(llm_websocket.send(message), timeout=10)
                logger.info("Message sent successfully")
            except asyncio.TimeoutError:
                logger.error("Timeout sending message to LLM service")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Increased delay
                continue
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"LLM service connection closed during send: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Increased delay
                    continue
                return None
                
            # Receive response with timeout
            try:
                logger.info("Waiting for LLM service response...")
                response = await asyncio.wait_for(llm_websocket.recv(), timeout=60)  # Increased timeout
                logger.info("Received response from LLM service")
                return response
            except asyncio.TimeoutError:
                logger.error("Timeout receiving response from LLM service")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Increased delay
                continue
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"LLM service connection closed during receive: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Increased delay
                    continue
                return None
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"LLM service connection closed: {e}")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(2)  # Increased delay
                continue
            return None
        except Exception as e:
            logger.error(f"Error forwarding to LLM: {e}")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(2)  # Increased delay
                continue
            return None
            
    logger.error("Max retries reached for LLM service communication")
    return None

# Handle WebSocket connections (with both websocket and path parameters)
async def handler(websocket):
    """Handler for WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}!",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send fake system context periodically
        context_task = asyncio.create_task(send_context_updates(websocket, client_id))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Handle ping messages
                if data.get('type') == 'ping':
                    if websocket.open:
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': datetime.now().isoformat()
                        }))
                    continue
                
                # Handle pong messages
                if data.get('type') == 'pong':
                    continue
                
                # Handle specific message types
                if data.get('type') == 'connection_established':
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    if websocket.open:
                        await websocket.send(json.dumps({
                            "type": "server_ready",
                            "payload": {
                                "status": "connected",
                                "server_version": "1.0.0",
                                "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                            }
                        }))
                elif data.get('type') in ['chat_message', 'user_message']:
                    # Forward to LLM service
                    logger.info(f"Forwarding message to LLM: {data}")
                    llm_response = await forward_to_llm(json.dumps({
                        "type": "chat_message",
                        "message": data.get('message', data.get('payload', {}).get('message', '')),
                        "timestamp": datetime.now().isoformat()
                    }))
                    if llm_response and websocket.open:
                        logger.info(f"Received LLM response: {llm_response}")
                        await websocket.send(llm_response)
                    else:
                        logger.error("No response from LLM service or connection closed")
                        if websocket.open:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {"message": "Failed to get response from LLM service"}
                            }))
                elif data.get('type') == 'agent_confirmation':
                    # Forward agent confirmation to LLM service for execution
                    logger.info(f"⚡ Forwarding agent confirmation to LLM service: {data}")
                    
                    # Preserve all the original data for proper routing
                    llm_response = await forward_to_llm(json.dumps(data))
                    
                    if llm_response and websocket.open:
                        logger.info(f"✅ Received agent execution response: {llm_response}")
                        await websocket.send(llm_response)
                        
                        # Send execution started notification to keep UI updated
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": data.get("session_id"),
                            "step": 1,
                            "progress": 20,
                            "message": "🚀 Execution started: Processing your request..."
                        }))
                    else:
                        logger.error("❌ No response from LLM service for agent confirmation")
                        if websocket.open:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {"message": "Failed to execute automation plan"}
                            }))
                elif data.get('type') == 'button_action':
                    # Forward button action to LLM service
                    logger.info(f"🔘 Forwarding button action to LLM service: {data}")
                    llm_response = await forward_to_llm(json.dumps(data))
                    
                    if llm_response and websocket.open:
                        logger.info(f"🔘 Received button action response: {llm_response}")
                        await websocket.send(llm_response)
                    else:
                        logger.error("❌ No response from LLM service for button action")
                        if websocket.open:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {"message": "Failed to process button action"}
                            }))
                else:
                    # Default echo response
                    if websocket.open:
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
                if websocket.open:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {"message": "Invalid JSON format"}
                    }))
                
        # Cancel context task when the loop breaks
        if not context_task.done():
            context_task.cancel()
            try:
                await context_task
            except asyncio.CancelledError:
                pass
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except asyncio.CancelledError:
        logger.info(f"Tasks for {client_id} cancelled")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_context_updates(websocket, client_id):
    """Send periodic context updates to simulate sensor data"""
    try:
        while True:
            # Check if connection is still open
            if not websocket.open:
                logger.info(f"Connection closed for {client_id}, stopping context updates")
                break
                
            # Create fake system context data
            context_data = {
                "type": "sensor_data",
                "payload": {
                    "timestamp": datetime.now().isoformat(),
                    "active_app": "Visual Studio Code",
                    "window_title": "project.py - Aiayer - VS Code",
                    "cpu_usage": 23.5,
                    "memory_usage": 42.8,
                    "processes": [
                        {"name": "Code", "id": 12345, "cpu": 12.3, "memory": 234.5},
                        {"name": "Chrome", "id": 12346, "cpu": 8.7, "memory": 412.8},
                        {"name": "Terminal", "id": 12347, "cpu": 1.2, "memory": 78.3}
                    ]
                }
            }
            
            try:
                if not websocket.open:
                    logger.info(f"Connection closed for {client_id}, stopping context updates")
                    break
                    
                # Send with timeout to prevent hanging
                try:
                    await asyncio.wait_for(
                        websocket.send(json.dumps(context_data)),
                        timeout=5
                    )
                    logger.debug(f"Sent context update to {client_id}")
                except websockets.exceptions.ConnectionClosed as e:
                    if e.code == 1001:  # Normal closure
                        logger.info(f"Client {client_id} disconnected normally")
                    else:
                        logger.info(f"Connection closed while sending to {client_id}: {e}")
                    break
                except asyncio.TimeoutError:
                    logger.error(f"Timeout sending context to {client_id}")
                    break
                except Exception as e:
                    logger.error(f"Error sending context to {client_id}: {e}")
                    break
                
            except websockets.exceptions.ConnectionClosed as e:
                if e.code == 1001:  # Normal closure
                    logger.info(f"Client {client_id} disconnected normally")
                else:
                    logger.info(f"Connection closed for {client_id}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error for {client_id}: {e}")
                break
                
            # Send every 10 seconds
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                logger.debug(f"Context updates for {client_id} cancelled")
                raise
            
    except asyncio.CancelledError:
        logger.debug(f"Context updates for {client_id} stopped")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in context updates for {client_id}: {e}")
        raise
    finally:
        logger.info(f"Context update task for {client_id} finished")
        # Ensure we remove the client from connected_clients if it's still there
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            logger.info(f"Removed {client_id} from connected clients")

async def main():
    # Bind to localhost on port 8768
    port = 8768
    host = "localhost"
    
    # Start server with proper WebSocket configuration
    logger.info(f"Starting WebSocket server on {host}:{port}")
    server = await websockets.serve(
        handler,
        host,
        port,
        ping_interval=30,  # Send ping every 30 seconds
        ping_timeout=90,   # Wait 90 seconds for pong
        close_timeout=30,  # Wait 30 seconds for clean closure
        max_size=10 * 1024 * 1024,  # 10MB max message size
        max_queue=32,      # Max message queue size
        compression=None   # Disable compression
    )
    
    # Save PID
    with open('pids/ws_server_8768.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)