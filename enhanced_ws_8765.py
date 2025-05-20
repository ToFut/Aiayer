#!/usr/bin/env python3
"""
Enhanced WebSocket Server on Port 8765 with LLM Integration
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import socket
import aiohttp
import random
import psutil
from datetime import datetime
import importlib.util
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aiayer.log'),
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
        
        # Initialize the LocalLLM instance
        llm_client = llm_module.LocalLLM(model_name="llava")
        
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

async def generate_response(query, context=None):
    """Generate a response to a user query using LocalLLM with memory context."""
    try:
        global memory_system, llm_client
        
        # Log the user message
        logger.info(f"📝 USER MESSAGE: {query}")
        
        # If memory system is initialized, get relevant context
        memory_context = {}
        if memory_system:
            try:
                # Get context summary from memory system
                memory_context = await memory_system.get_context_summary()
                logger.info(f"🔍 MEMORY CONTEXT RETRIEVED:")
                logger.info(f"  - Active window: {memory_context.get('window', 'Unknown')}")
                logger.info(f"  - Active apps: {memory_context.get('active_apps', [])}")
                logger.info(f"  - Screen content length: {len(memory_context.get('screen_content', ''))}")
                logger.info(f"  - Recent messages count: {len(memory_context.get('recent_messages', []))}")
                
                # Search for relevant memories
                relevant_memories = await memory_system.search_memory(query, limit=3)
                if relevant_memories:
                    memory_context['relevant_memories'] = relevant_memories
                    logger.info(f"  - Found {len(relevant_memories)} relevant memories")
            except Exception as memory_ex:
                logger.error(f"Error retrieving memory context: {memory_ex}")
                logger.error(traceback.format_exc())
        
        # Combine the provided context with memory context
        combined_context = {}
        if context:
            combined_context.update(context)
        if memory_context:
            combined_context.update(memory_context)
            
        # Log the final prompt that will be sent to the LLM
        logger.info(f"🤖 FINAL PROMPT TO LLM:")
        logger.info(f"  - Query: {query}")
        logger.info(f"  - Combined context keys: {list(combined_context.keys())}")
        logger.info(f"  - Context size: {len(str(combined_context))} chars")
        
        # Generate response using LLM
        response = await llm_client.generate_response([{
            "role": "user",
            "content": query
        }])
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        logger.error(traceback.format_exc())
        return f"Error: {str(e)}"

async def process_user_interaction(message_data, websocket):
    """Process a user interaction message"""
    global memory_system, context_data
    
    payload = message_data.get('payload', {})
    
    if payload.get('type') == 'query':
        query = payload.get('query', '')
        logger.info(f"Processing query: {query}")
        
        # If we have a memory system, store the user query
        if memory_system:
            try:
                await memory_system.add_message({
                    "type": "user_query",
                    "content": query,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Stored user query in memory: {query}")
            except Exception as e:
                logger.error(f"Error storing user query in memory: {e}")
        
        # Generate a response using both context_data and memory
        response_data = await generate_response(query, context_data)
        
        # Send back to the client
        await websocket.send(json.dumps(response_data))
        logger.info(f"Sent response for query: {query}")
    elif payload.get('type') == 'sensor_data':
        # If we have sensor data, store it in the memory system
        logger.info(f"Received sensor data of type: {payload.get('sensor_type', 'unknown')}")
        
        sensor_type = payload.get('sensor_type')
        sensor_data = payload.get('data', {})
        
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
    else:
        # Echo back with timestamp for other interaction types
        await websocket.send(json.dumps({
            "type": "echo",
            "data": message_data,
            "timestamp": datetime.now().isoformat()
        }))

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
                        "llm_model": "llava" if llm_client else None,
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
                    
                    memory_metrics = {
                        "memory_system_active": True,
                        "memory_usage_mb": round(memory_usage_mb, 2),
                        "conversation_length": len(memory_system.conversation_memory.messages) if hasattr(memory_system, 'conversation_memory') else 0,
                        "context_entries": len(memory_system.context_memory.context_history) if hasattr(memory_system, 'context_memory') else 0
                    }
                except Exception as e:
                    logger.error(f"Error getting memory metrics: {e}")
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
                    "llm_model": "llava" if llm_client else None,
                    "context_data_size": len(str(context_data)),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(10)

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Initialize memory system first
        if not await initialize_memory_system():
            logger.error("Failed to initialize memory system. Exiting...")
            return
        
        # Initialize LLM service
        if not await initialize_llm_service():
            logger.warning("Failed to initialize LLM service. Continuing without LLM support...")
        
        # Start WebSocket server
        port = 8765
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use. Exiting...")
            return
            
        async with websockets.serve(handler, "localhost", port):
            logger.info(f"WebSocket server started on port {port}")
            
            # Start status broadcast task
            broadcast_task = asyncio.create_task(broadcast_status())
            
            # Keep the server running
            await asyncio.Future()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())

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
        sys.exit(1)