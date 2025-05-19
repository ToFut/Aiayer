#!/usr/bin/env python3
"""
Fixed WebSocket Server on Port 8765 with Memory Integration and LocalLLM
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import socket
import random
import psutil
import traceback
import importlib.util
from datetime import datetime
from typing import Optional, Dict
import base64
import uuid

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
llm_client = None
memory_system = None
context_data = {}

async def initialize_memory_system():
    """Initialize the memory system for context-aware responses."""
    global memory_system
    
    try:
        logger.info("Initializing memory system...")
        
        # Dynamically import memory system
        spec = importlib.util.spec_from_file_location(
            "memory_system", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "memory/memory_system.py")
        )
        memory_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(memory_module)
        
        # Initialize the memory system
        memory_system = memory_module.MemorySystem()
        await memory_system.initialize()
        
        logger.info("Memory system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        logger.error(traceback.format_exc())
        return False

async def initialize_llm_service():
    """Initialize the advanced LLM service using the LocalLLM implementation."""
    global llm_client
    
    try:
        # Import the LocalLLM class
        logger.info("Initializing advanced LLM service...")
        
        # Dynamically import LocalLLM
        spec = importlib.util.spec_from_file_location(
            "model", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "llm/model.py")
        )
        llm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_module)
        
        # Initialize the LocalLLM instance with ollama3.2:latest
        llm_client = llm_module.LocalLLM(model_name="ollama3.2:latest")
        
        # Make sure the model is available
        logger.info("Checking LLM model availability...")
        await llm_client.initialize()
        
        logger.info("Advanced LLM service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing advanced LLM service: {e}")
        logger.error(traceback.format_exc())
        llm_client = None
        return False

# Initialize screen sensor LLM
try:
    screen_llm = llm_module.LocalLLM(model_name="llava")
    logger.info("Screen sensor LLM initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize screen sensor LLM: {e}")
    screen_llm = None

async def generate_response(query: str, context: Optional[Dict] = None) -> str:
    """
    Generate a response using the LLM service.
    
    Args:
        query (str): The user's query
        context (Optional[Dict]): Additional context for the response
        
    Returns:
        str: Generated response
    """
    if not llm_client:
        logger.error("LLM client not initialized")
        return "I apologize, but I'm currently unable to process your request. Please try again later."
        
    try:
        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": query}
        ]
        
        # Add context if available
        if context:
            context_str = json.dumps(context)
            messages[0]["content"] += f"\nContext: {context_str}"
            
        # Generate response
        response = await llm_client.generate_response(messages)
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."

async def process_screen_sensor(image_data: bytes) -> str:
    """
    Process screen sensor data using the LLaVA model.
    
    Args:
        image_data (bytes): The image data to process
        
    Returns:
        str: Generated response
    """
    if not screen_llm:
        logger.error("Screen sensor LLM not initialized")
        return "Screen sensor is currently unavailable."
        
    try:
        # Prepare messages for the LLaVA model
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant that can analyze images."},
            {"role": "user", "content": "What do you see in this image?", "image": image_data}
        ]
        
        # Generate response
        response = await screen_llm.generate_response(messages)
        return response
        
    except Exception as e:
        logger.error(f"Error processing screen sensor data: {e}")
        return "I apologize, but I encountered an error while processing the screen data. Please try again."

async def process_user_interaction(message_data, websocket):
    """
    Process a user interaction message and generate a response.
    
    Args:
        message_data (dict): The message data from the client
        websocket: The WebSocket connection
    """
    try:
        # Extract message type and content
        message_type = message_data.get('type')
        logger.info(f"Processing message type: {message_type}")
        
        # Handle different message types
        if message_type == 'user_interaction':
            # Try to get content from different possible formats
            content = None
            if 'content' in message_data:
                content = message_data['content']
            elif 'payload' in message_data:
                payload = message_data['payload']
                if isinstance(payload, dict):
                    content = payload.get('query') or payload.get('content')
            
            if not content:
                logger.error("No content found in message")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'content': 'No message content provided'
                }))
                return
                
            logger.info(f"Processing user message: {content}")
            
            # Generate response for chat message
            response = await generate_response(content)
            logger.info(f"Generated response: {response[:100]}...")
            
            await websocket.send(json.dumps({
                'type': 'llm_response',
                'content': response
            }))
            
        elif message_type == 'screen_sensor':
            # Process screen sensor data
            try:
                content = message_data.get('content')
                if not content:
                    raise ValueError("No image data provided")
                    
                image_data = base64.b64decode(content)
                response = await process_screen_sensor(image_data)
                await websocket.send(json.dumps({
                    'type': 'screen_analysis',
                    'content': response
                }))
            except Exception as e:
                logger.error(f"Error processing screen sensor data: {e}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'content': 'Failed to process screen data'
                }))
                
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket.send(json.dumps({
                'type': 'error',
                'content': f'Unknown message type: {message_type}'
            }))
            
    except Exception as e:
        logger.error(f"Error processing user interaction: {e}")
        logger.error(traceback.format_exc())
        await websocket.send(json.dumps({
            'type': 'error',
            'content': 'Internal server error'
        }))

async def websocket_handler(websocket, path):
    """
    Handle WebSocket connections and messages.
    
    Args:
        websocket: The WebSocket connection
        path: The request path
    """
    client_id = str(uuid.uuid4())
    logger.info(f"New WebSocket connection: {client_id}")
    
    try:
        # Send connection confirmation
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                message_data = json.loads(message)
                await process_user_interaction(message_data, websocket)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message from client {client_id}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'content': 'Invalid message format'
                }))
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'content': 'Internal server error'
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket connection closed: {client_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket handler for client {client_id}: {e}")
    finally:
        logger.info(f"Cleaning up connection: {client_id}")

async def handler(websocket):
    """Handle WebSocket connections."""
    global memory_system, context_data
    
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message with information about available systems
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to WebSocket server",
                "memory_system_active": memory_system is not None,
                "advanced_llm_initialized": llm_client is not None,
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data.get('type', 'unknown_type')}")
                
                # Process different message types
                if data.get('type') == 'user_interaction':
                    await process_user_interaction(data, websocket)
                elif data.get('type') == 'context_update':
                    # Update our context data
                    new_context = data.get('payload', {})
                    context_data.update(new_context)
                    logger.info("Context data updated")
                    
                    # If we have a memory system, update context there too
                    if memory_system:
                        try:
                            # Determine sensor type from the context data
                            sensor_type = new_context.get('sensor_type', 'unknown')
                            sensor_data = new_context.get('data', {})
                            
                            if sensor_type and sensor_data:
                                await memory_system.process_sensor_data(sensor_type, sensor_data)
                                logger.info(f"Updated memory system with context data for sensor: {sensor_type}")
                        except Exception as e:
                            logger.error(f"Error updating memory system with context: {e}")
                    
                    # Acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "context_update_received",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif data.get('type') == 'sensor_data':
                    # Process sensor data
                    sensor_payload = data.get('payload', {})
                    sensor_type = sensor_payload.get('sensor_type', 'unknown')
                    sensor_data = sensor_payload.get('data', {})
                    
                    # Update context data
                    if sensor_type:
                        context_data[sensor_type] = sensor_data
                    
                    # If we have a memory system, process the sensor data
                    if memory_system and sensor_type:
                        try:
                            await memory_system.process_sensor_data(sensor_type, sensor_data)
                            logger.info(f"Processed {sensor_type} sensor data in memory system")
                        except Exception as e:
                            logger.error(f"Error processing sensor data in memory: {e}")
                    
                    # Acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "sensor_data_received",
                        "payload": {
                            "sensor_type": sensor_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                elif data.get('type') == 'memory_query':
                    # Handle memory query requests
                    query = data.get('payload', {}).get('query', '')
                    limit = data.get('payload', {}).get('limit', 5)
                    
                    if memory_system and query:
                        try:
                            results = await memory_system.search_memory(query, limit)
                            await websocket.send(json.dumps({
                                "type": "memory_query_results",
                                "payload": {
                                    "query": query,
                                    "results": results,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                            logger.info(f"Sent memory query results for: {query}")
                        except Exception as e:
                            logger.error(f"Error searching memory: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Error searching memory: {str(e)}"
                            }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Memory system not available or query is empty"
                        }))
                elif data.get('type') == 'status_request':
                    # Send status information
                    status_data = {
                        "memory_system_active": memory_system is not None,
                        "advanced_llm_initialized": llm_client is not None,
                        "llm_model": "ollama3.2:latest" if llm_client else None,
                        "connected_clients": len(connected_clients),
                        "context_data_size": len(str(context_data)),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps({
                        "type": "status_response",
                        "payload": status_data
                    }))
                    logger.info("Sent status information")
                else:
                    # Echo back with timestamp for other message types
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                logger.error(traceback.format_exc())
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Error processing message: {str(e)}"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    global memory_system, llm_client
    
    while True:
        if connected_clients:
            # Get memory system metrics if available
            memory_metrics = {}
            if memory_system:
                try:
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                    
                    # Safely get memory metrics with extra error handling
                    conversation_length = 0
                    context_entries = 0
                    
                    try:
                        if hasattr(memory_system, 'conversation_memory') and hasattr(memory_system.conversation_memory, 'messages'):
                            conversation_length = len(memory_system.conversation_memory.messages)
                    except Exception as msg_err:
                        logger.error(f"Error accessing conversation messages: {msg_err}")
                        
                    try:
                        if hasattr(memory_system, 'context_memory') and hasattr(memory_system.context_memory, 'context_history'):
                            context_entries = len(memory_system.context_memory.context_history)
                    except Exception as ctx_err:
                        logger.error(f"Error accessing context history: {ctx_err}")
                    
                    memory_metrics = {
                        "memory_system_active": True,
                        "memory_usage_mb": round(memory_usage_mb, 2),
                        "conversation_length": conversation_length,
                        "context_entries": context_entries
                    }
                except Exception as e:
                    logger.error(f"Error getting memory metrics: {e}")
                    logger.error(traceback.format_exc())  # Add stack trace for better debugging
                    memory_metrics = {"memory_system_active": True, "error": str(e)}
            else:
                memory_metrics = {"memory_system_active": False}
            
            # Create status message
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "memory_system": memory_metrics,
                    "advanced_llm_initialized": llm_client is not None,
                    "llm_model": "ollama3.2:latest" if llm_client else None,
                    "context_data_size": len(str(context_data)),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            try:
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients],
                    return_exceptions=True
                )
            except Exception as send_error:
                logger.error(f"Error sending status updates: {send_error}")
        
        await asyncio.sleep(10)

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

async def main():
    """Main function to start the WebSocket server."""
    try:
        global memory_system, llm_client
        
        # Use port 8765 to match the Tauri app's expectation
        port = 8765
        
        # Check if port is in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            
            # Try to forcefully release the port by killing any process using it
            os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
            os.system(f"pkill -f 'port {port}' 2>/dev/null || true")
            
            # Wait a moment for the port to be released
            await asyncio.sleep(1)
            
            # Check again
            if is_port_in_use(port):
                logger.error("Failed to release port")
                sys.exit(1)
        
        # Initialize memory system
        logger.info("Initializing memory system...")
        memory_initialized = await initialize_memory_system()
        if memory_initialized:
            logger.info("Memory system initialized successfully")
        else:
            logger.warning("Memory system initialization failed, will use fallback responses")
            
        # Initialize advanced LLM service
        logger.info("Initializing advanced LLM service...")
        llm_initialized = await initialize_llm_service()
        if llm_initialized:
            logger.info("Advanced LLM service initialized successfully")
        else:
            logger.warning("Advanced LLM service initialization failed, will use fallback responses")
                
        # Create the server
        server = await websockets.serve(
            handler,
            "0.0.0.0",  # Bind to all interfaces
            port,
            ping_interval=10,
            ping_timeout=5
        )
        
        logger.info(f"WebSocket server started on ws://0.0.0.0:{port}")
        logger.info(f"Memory system: {'ACTIVE' if memory_system else 'INACTIVE'}")
        logger.info(f"Advanced LLM service: {'INITIALIZED' if llm_client else 'NOT AVAILABLE'}")
        
        # Save PID to file
        os.makedirs('pids', exist_ok=True)
        with open('pids/ws_server_8765.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)