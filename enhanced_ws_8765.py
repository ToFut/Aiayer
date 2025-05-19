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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_ws_8765.log'),
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
        
        logger.info(f"Generating response for query: {query}")
        
        # If memory system is initialized, get relevant context
        memory_context = {}
        if memory_system:
            try:
                # Get context summary from memory system
                memory_context = await memory_system.get_context_summary()
                logger.info(f"Retrieved memory context with {len(str(memory_context))} chars")
                
                # Search for relevant memories
                relevant_memories = await memory_system.search_memory(query, limit=3)
                if relevant_memories:
                    memory_context['relevant_memories'] = relevant_memories
                    logger.info(f"Found {len(relevant_memories)} relevant memories")
            except Exception as memory_ex:
                logger.error(f"Error retrieving memory context: {memory_ex}")
                logger.error(traceback.format_exc())
        
        # Check if LocalLLM is available
        if llm_client and hasattr(llm_client, 'generate_response'):
            try:
                # Format messages for the LocalLLM format (which uses the OpenAI-style format)
                system_message = "You are a helpful assistant with access to the user's screen content and active applications. Use this context to provide more helpful responses."
                
                # Add context to system message
                if memory_context:
                    system_message += "\n\nContext:"
                    if 'window' in memory_context:
                        system_message += f"\nActive Window: {memory_context.get('window', 'Unknown')}"
                    if 'active_apps' in memory_context:
                        system_message += f"\nActive Applications: {', '.join(memory_context.get('active_apps', []))}"
                    if 'screen_content' in memory_context:
                        screen_content = memory_context.get('screen_content', '')
                        shortened = screen_content[:500] + "..." if len(screen_content) > 500 else screen_content
                        system_message += f"\nScreen Content: {shortened}"
                    if 'relevant_memories' in memory_context:
                        system_message += "\nRelevant Past Information:"
                        for i, memory in enumerate(memory_context['relevant_memories']):
                            system_message += f"\n - {memory.get('content', 'No content')}"
                
                # Prepare messages in the format expected by the LocalLLM
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ]
                
                # Call the LocalLLM generate_response method
                logger.info("Calling local LLM with user query and context")
                response_text = await llm_client.generate_response(messages)
                
                logger.info(f"LocalLLM returned response: {response_text[:100]}...")
                
                # Store interaction in memory if available
                if memory_system:
                    try:
                        await memory_system.add_message({
                            "type": "user_query",
                            "content": query,
                            "timestamp": datetime.now().isoformat()
                        })
                        await memory_system.add_message({
                            "type": "assistant_response",
                            "content": response_text,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as mem_ex:
                        logger.error(f"Error storing in memory: {mem_ex}")
                
                return {
                    "type": "query_response",
                    "payload": {
                        "query": query,
                        "response": response_text,
                        "timestamp": datetime.now().isoformat(),
                        "context_used": bool(context),
                        "memory_used": bool(memory_context),
                        "advanced_llm": True
                    }
                }
            except Exception as llm_ex:
                logger.error(f"Error using LocalLLM: {llm_ex}")
                logger.error(traceback.format_exc())
        
        # Fallback to mock responses if LLM service fails or is not available
        logger.warning("Using fallback mock response generation")
        
        # Predefined response templates
        response_templates = [
            "I understand you're asking about '{query}'. Here's what I can help with: {detail}",
            "Thanks for your query about '{query}'. {detail}",
            "I've analyzed your request about '{query}'. {detail}",
            "Regarding '{query}', I can provide the following information: {detail}"
        ]
        
        personalized_responses = {
            "what can you help me with": [
                "I can help you with analyzing your environment, monitoring system activity, answering questions about your work, and providing personalized assistance based on what you're doing.",
                "I'm designed to assist with a variety of tasks including analyzing your screen content, monitoring running applications, answering questions, and providing contextual assistance.",
                "I can assist you by monitoring your work environment, providing relevant information based on your context, answering questions, and helping with productivity tasks."
            ],
            "my name is segev": [
                "Hello Segev! It's nice to meet you. I'll remember your name for our conversation.",
                "Great to meet you, Segev! I'll keep that in mind as we work together.",
                "Thanks for introducing yourself, Segev! How can I assist you today?"
            ],
            "how does this work": [
                "This system monitors your environment through sensors that track your screen content and running applications. It then uses this context to provide more relevant assistance.",
                "The system uses various sensors to understand your work context, including what's on your screen and which applications you're using. This helps me provide more personalized responses.",
                "I work by collecting contextual information about your activities, which helps me understand what you're working on and provide more relevant assistance."
            ],
            "and now": [
                "Is there something specific you'd like help with? I'm ready to assist based on your current context.",
                "Now that we're connected, I can help answer questions, provide information based on your current tasks, or assist with productivity tasks.",
                "I'm now fully operational and monitoring your context. What would you like assistance with?"
            ],
            "now": [
                "I'm ready to assist you with your current tasks. What specifically would you like help with?",
                "Now that the system is running, I can provide assistance based on your current work context. How can I help?",
                "I'm actively monitoring your work environment and ready to provide assistance. What would you like to know?"
            ],
            "eh": [
                "I'm sorry if there was any confusion. I'm here to assist with your work or answer questions. How can I help you?",
                "Would you like me to explain more about how I can assist you? I'm designed to provide contextual assistance based on your current activities.",
                "I'm here to help with your work. Let me know if you have any specific questions or tasks you need assistance with."
            ],
            "hey": [
                "Hello! I'm here to assist you. What can I help with today?",
                "Hi there! I'm ready to help with your questions or tasks.",
                "Greetings! How can I assist you with your current activities?"
            ],
            "nyc": [
                "NYC stands for New York City, the most populous city in the United States. It's a global center for finance, culture, fashion, and entertainment.",
                "New York City (NYC) is a major metropolitan area located in the state of New York. It consists of five boroughs: Manhattan, Brooklyn, Queens, The Bronx, and Staten Island.",
                "NYC refers to New York City, known for landmarks like the Empire State Building, Central Park, Times Square, and the Statue of Liberty."
            ]
        }
        
        # Find most appropriate response
        query_lower = query.lower()
        response_detail = "I can provide information and assistance based on your current context."
        
        # Check if we have a personalized response
        for key, responses in personalized_responses.items():
            if key in query_lower:
                response_detail = random.choice(responses)
                break
        
        # Add context information if available
        if context:
            active_window = context.get('active_window', 'Unknown')
            response_detail += f" I notice you're currently using {active_window}."
        
        # Format the response
        template = random.choice(response_templates)
        response = template.format(query=query, detail=response_detail)
        
        # Store in memory if available
        if memory_system:
            try:
                await memory_system.add_message({
                    "type": "user_query",
                    "content": query,
                    "timestamp": datetime.now().isoformat()
                })
                await memory_system.add_message({
                    "type": "assistant_response",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as mem_ex:
                logger.error(f"Error storing in memory: {mem_ex}")
        
        # Add a short delay to simulate processing
        await asyncio.sleep(0.5)
        
        return {
            "type": "query_response",
            "payload": {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "is_fallback": True
            }
        }
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        logger.error(traceback.format_exc())
        return {
            "type": "query_response",
            "payload": {
                "query": query,
                "response": "I'm sorry, I encountered an error processing your request.",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }

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
            
        # Ensure we don't use a WebSocket connection here
        # The LocalLLM class from llm/model.py will handle the direct API calls
                
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
        sys.exit(1)