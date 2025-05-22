#!/usr/bin/env python3
"""
Context Memory WebSocket Server
Provides enhanced context to LLM services through a WebSocket interface.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import time

# Import the enhanced context memory components
from llava_visual_processor import LLaVAVisualProcessor
from enhanced_context_memory import EnhancedContextMemory
from memory_context_integration import MemoryContextIntegration

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/context_memory_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('context_memory_server')

# WebSocket server configuration
WS_HOST = "localhost"
WS_PORT = 8769  # Different port than bridge server (8767)

# Global variables
connected_clients = set()
enhanced_context = None
memory_integration = None
llava_processor = None
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

async def initialize_components():
    """Initialize all memory system components"""
    global enhanced_context, memory_integration, llava_processor
    
    try:
        logger.info("Initializing LLaVA Visual Processor...")
        llava_processor = LLaVAVisualProcessor()
        
        logger.info("Initializing Enhanced Context Memory...")
        enhanced_context = EnhancedContextMemory(llava_processor=llava_processor)
        
        # Mock memory system for now - could be replaced with real one
        class MockMemorySystem:
            async def add_sensor_data(self, sensor_type, data):
                logger.info(f"Mock memory system: Adding {sensor_type} data")
                return True
        
        logger.info("Initializing Memory Context Integration...")
        memory_integration = MemoryContextIntegration(MockMemorySystem())
        await memory_integration.start()
        
        logger.info("All components initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        logger.error(traceback.format_exc())
        return False

async def handle_bridge_data(data):
    """Process data from bridge server"""
    if not memory_integration:
        logger.warning("Memory integration not initialized")
        return False
    
    try:
        msg_type = data.get('type')
        
        if msg_type == 'sensor_data':
            payload = data.get('payload', {})
            # Update our local copy of sensor data
            global sensor_data
            sensor_data = payload
            
            # Process each type of sensor data
            if "screen" in payload:
                await memory_integration.add_sensor_data("screen", payload["screen"])
                
            if "processes" in payload:
                await memory_integration.add_sensor_data("process", {
                    "active_apps": payload["processes"],
                    "active_window": payload.get("screen", {}).get("active_window", "")
                })
                
            if "files" in payload:
                await memory_integration.add_sensor_data("file", {
                    "files": payload["files"]
                })
                
            return True
            
    except Exception as e:
        logger.error(f"Error handling bridge data: {e}")
        logger.error(traceback.format_exc())
        return False

async def connect_to_bridge_server():
    """Connect to the bridge server to get sensor data"""
    bridge_uri = "ws://localhost:8767"
    
    while True:
        try:
            logger.info(f"Connecting to bridge server at {bridge_uri}")
            async with websockets.connect(bridge_uri) as websocket:
                logger.info("Connected to bridge server")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "context_memory_server",
                        "version": "1.0.0",
                        "capabilities": ["context_processing", "enhanced_memory"]
                    }
                }))
                
                # Main message loop
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Process data from bridge server
                        await handle_bridge_data(data)
                            
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Bridge server connection closed")
                        break
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON from bridge server")
                    except Exception as e:
                        logger.error(f"Error processing message from bridge server: {e}")
                        logger.error(traceback.format_exc())
                        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Bridge server connection failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error connecting to bridge server: {e}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)

async def handler(websocket):
    """WebSocket connection handler for context memory clients"""
    client_id = f"client_{id(websocket)}"
    client_type = "unknown"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Enhanced Context Memory System",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client', 'unknown')
                    logger.info(f"Client {client_id} identified as: {client_type}")
                    
                    # Send ready confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "server_time": datetime.now().isoformat(),
                            "capabilities": ["enhanced_context", "visual_understanding", "activity_tracking"]
                        }
                    }))
                
                elif msg_type == 'get_enhanced_context':
                    # Client is requesting current enhanced context
                    if memory_integration:
                        context = await memory_integration.get_enhanced_context()
                        
                        # Send enhanced context
                        await websocket.send(json.dumps({
                            "type": "enhanced_context",
                            "payload": context,
                            "timestamp": datetime.now().isoformat()
                        }))
                        logger.info(f"Sent enhanced context to {client_id} ({len(json.dumps(context))} bytes)")
                    else:
                        # No context available, send empty response
                        await websocket.send(json.dumps({
                            "type": "enhanced_context",
                            "payload": {},
                            "error": "Context memory system not initialized",
                            "timestamp": datetime.now().isoformat()
                        }))
                        logger.warning(f"No context available for {client_id}")
                
                elif msg_type == 'sensor_data':
                    # Client is sending sensor data directly
                    payload = data.get('payload', {})
                    sensor_type = payload.get('sensor_type')
                    sensor_data = payload.get('data')
                    
                    if memory_integration and sensor_type and sensor_data:
                        await memory_integration.add_sensor_data(sensor_type, sensor_data)
                        await websocket.send(json.dumps({
                            "type": "sensor_data_received",
                            "payload": {"success": True, "sensor_type": sensor_type},
                            "timestamp": datetime.now().isoformat()
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "sensor_data_received",
                            "payload": {"success": False, "error": "Invalid sensor data or memory system not initialized"},
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif msg_type == 'analyze_image':
                    # Client is requesting image analysis
                    payload = data.get('payload', {})
                    image_data = payload.get('image')
                    
                    if llava_processor and image_data:
                        # Process image with LLaVA
                        analysis = await llava_processor.analyze_screen(image_data)
                        await websocket.send(json.dumps({
                            "type": "image_analysis",
                            "payload": analysis,
                            "timestamp": datetime.now().isoformat()
                        }))
                        logger.info(f"Sent image analysis to {client_id}")
                    else:
                        await websocket.send(json.dumps({
                            "type": "image_analysis",
                            "payload": {"error": "LLaVA processor not initialized or no image data"},
                            "timestamp": datetime.now().isoformat()
                        }))
                
                else:
                    # Default echo response
                    response = {
                        "type": "echo",
                        "payload": {
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients)
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def status_updates():
    """Send periodic status updates with current context stats"""
    while True:
        if connected_clients and memory_integration:
            try:
                # Get basic context stats
                context = await memory_integration.get_enhanced_context()
                
                stats = {
                    "current_app": context.get("current_application", {}).get("name", "unknown"),
                    "activities": len(context.get("recent_activities", [])),
                    "has_screen_context": bool(context.get("screen_context")),
                    "sensor_data_timestamp": sensor_data.get("last_update", "")
                }
                
                await broadcast({
                    "type": "status_update",
                    "payload": stats,
                    "timestamp": datetime.now().isoformat()
                })
                logger.debug(f"Status update sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending status update: {e}")
        
        await asyncio.sleep(60)  # Status update every minute

async def main():
    """Main function to start the WebSocket server"""
    try:
        # Initialize memory components
        success = await initialize_components()
        if not success:
            logger.error("Failed to initialize memory components, server will have limited functionality")
        
        # Start the WebSocket server
        logger.info(f"Starting context memory WebSocket server on {WS_HOST}:{WS_PORT}")
        async with websockets.serve(handler, WS_HOST, WS_PORT):
            logger.info(f"Context memory server started successfully on port {WS_PORT}")
            
            # Save PID
            os.makedirs("pids", exist_ok=True)
            with open('pids/context_memory_server.pid', 'w') as f:
                f.write(str(os.getpid()))
            
            # Start heartbeat and status update tasks
            heartbeat_task = asyncio.create_task(heartbeat())
            status_task = asyncio.create_task(status_updates())
            
            # Connect to bridge server to get sensor data
            bridge_task = asyncio.create_task(connect_to_bridge_server())
            
            # Keep the server running
            await asyncio.Future()
            
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)