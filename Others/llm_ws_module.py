#!/usr/bin/env python3
"""
LLM WebSocket Module for Integration with start_optimized_system_fixed.sh
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

class LLMWebSocketServer:
    """
    WebSocket server that integrates with LocalLLM for processing user messages.
    This class is designed to be used with start_optimized_system_fixed.sh.
    """
    
    def __init__(self, port=8765, host="0.0.0.0"):
        """Initialize the WebSocket server with LocalLLM integration."""
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        os.makedirs("pids", exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('logs/llm_ws_module.log')
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        # Server configuration
        self.port = port
        self.host = host
        
        # Track connected clients
        self.connected_clients = set()
        self.llm_client = None
        self.memory_system = None
        self.context_data = {}
    
    async def initialize_memory_system(self):
        """Initialize the memory system for context-aware responses."""
        try:
            self.logger.info("Initializing memory system...")
            
            # Dynamically import memory system
            spec = importlib.util.spec_from_file_location(
                "memory_system", 
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "memory/memory_system.py")
            )
            memory_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(memory_module)
            
            # Initialize the memory system
            self.memory_system = memory_module.MemorySystem()
            await self.memory_system.initialize()
            
            self.logger.info("Memory system initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing memory system: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    async def initialize_llm_service(self):
        """Initialize the advanced LLM service using the LocalLLM implementation."""
        try:
            # Import the LocalLLM class
            self.logger.info("Initializing advanced LLM service...")
            
            # Dynamically import LocalLLM
            spec = importlib.util.spec_from_file_location(
                "model", 
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "llm/model.py")
            )
            llm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(llm_module)
            
            # Initialize the LocalLLM instance
            self.llm_client = llm_module.LocalLLM(model_name="llava")
            
            # Make sure the model is available
            self.logger.info("Checking LLM model availability...")
            await self.llm_client.initialize()
            
            self.logger.info("Advanced LLM service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing advanced LLM service: {e}")
            self.logger.error(traceback.format_exc())
            self.llm_client = None
            return False
    
    async def generate_response(self, query, context=None):
        """Generate a response to a user query using LocalLLM with memory context."""
        try:
            self.logger.info(f"Generating response for query: {query}")
            
            # If memory system is initialized, get relevant context
            memory_context = {}
            if self.memory_system:
                try:
                    # Get context summary from memory system
                    memory_context = await self.memory_system.get_context_summary()
                    self.logger.info(f"Retrieved memory context with {len(str(memory_context))} chars")
                    
                    # Search for relevant memories
                    relevant_memories = await self.memory_system.search_memory(query, limit=3)
                    if relevant_memories:
                        memory_context['relevant_memories'] = relevant_memories
                        self.logger.info(f"Found {len(relevant_memories)} relevant memories")
                except Exception as memory_ex:
                    self.logger.error(f"Error retrieving memory context: {memory_ex}")
                    self.logger.error(traceback.format_exc())
            
            # Check if LocalLLM is available
            if self.llm_client and hasattr(self.llm_client, 'generate_response'):
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
                    self.logger.info("Calling local LLM with user query and context")
                    response_text = await self.llm_client.generate_response(messages)
                    
                    self.logger.info(f"LocalLLM returned response: {response_text[:100]}...")
                    
                    # Store interaction in memory if available
                    if self.memory_system:
                        try:
                            await self.memory_system.add_message({
                                "type": "user_query",
                                "content": query,
                                "timestamp": datetime.now().isoformat()
                            })
                            await self.memory_system.add_message({
                                "type": "assistant_response",
                                "content": response_text,
                                "timestamp": datetime.now().isoformat()
                            })
                        except Exception as mem_ex:
                            self.logger.error(f"Error storing in memory: {mem_ex}")
                    
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
                    self.logger.error(f"Error using LocalLLM: {llm_ex}")
                    self.logger.error(traceback.format_exc())
            
            # Fallback to mock responses if LLM service fails or is not available
            self.logger.warning("Using fallback mock response generation")
            
            # Predefined response templates
            response_templates = [
                "I understand you're asking about '{query}'. Here's what I can help with: {detail}",
                "Thanks for your query about '{query}'. {detail}",
                "I've analyzed your request about '{query}'. {detail}",
                "Regarding '{query}', I can provide the following information: {detail}"
            ]
            
            # Find most appropriate response
            query_lower = query.lower()
            response_detail = "I can provide information and assistance based on your current context."
            
            # Add context information if available
            if context:
                active_window = context.get('active_window', 'Unknown')
                response_detail += f" I notice you're currently using {active_window}."
            
            # Format the response
            template = random.choice(response_templates)
            response = template.format(query=query, detail=response_detail)
            
            # Store in memory if available
            if self.memory_system:
                try:
                    await self.memory_system.add_message({
                        "type": "user_query",
                        "content": query,
                        "timestamp": datetime.now().isoformat()
                    })
                    await self.memory_system.add_message({
                        "type": "assistant_response",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as mem_ex:
                    self.logger.error(f"Error storing in memory: {mem_ex}")
            
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
            self.logger.error(f"Error generating response: {e}")
            self.logger.error(traceback.format_exc())
            return {
                "type": "query_response",
                "payload": {
                    "query": query,
                    "response": "I'm sorry, I encountered an error processing your request.",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            }
    
    async def process_user_interaction(self, message_data, websocket):
        """Process a user interaction message"""
        payload = message_data.get('payload', {})
        
        if payload.get('type') == 'query':
            query = payload.get('query', '')
            self.logger.info(f"Processing query: {query}")
            
            # If we have a memory system, store the user query
            if self.memory_system:
                try:
                    await self.memory_system.add_message({
                        "type": "user_query",
                        "content": query,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.logger.info(f"Stored user query in memory: {query}")
                except Exception as e:
                    self.logger.error(f"Error storing user query in memory: {e}")
            
            # Generate a response using both context_data and memory
            response_data = await self.generate_response(query, self.context_data)
            
            # Send back to the client
            await websocket.send(json.dumps(response_data))
            self.logger.info(f"Sent response for query: {query}")
        elif payload.get('type') == 'sensor_data':
            # If we have sensor data, store it in the memory system
            self.logger.info(f"Received sensor data of type: {payload.get('sensor_type', 'unknown')}")
            
            sensor_type = payload.get('sensor_type')
            sensor_data = payload.get('data', {})
            
            # Update context data
            if sensor_type:
                self.context_data[sensor_type] = sensor_data
            
            # If we have a memory system, process the sensor data
            if self.memory_system and sensor_type:
                try:
                    await self.memory_system.process_sensor_data(sensor_type, sensor_data)
                    self.logger.info(f"Processed {sensor_type} sensor data in memory system")
                except Exception as e:
                    self.logger.error(f"Error processing sensor data in memory: {e}")
            
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
    
    async def handler(self, websocket):
        """Handle WebSocket connections."""
        try:
            # Add client to set
            self.connected_clients.add(websocket)
            client_id = id(websocket)
            self.logger.info(f"Client {client_id} connected")
            
            # Send welcome message with information about available systems
            await websocket.send(json.dumps({
                "type": "connection_established",
                "data": {
                    "message": "Connected to WebSocket server with LocalLLM integration",
                    "memory_system_active": self.memory_system is not None,
                    "advanced_llm_initialized": self.llm_client is not None,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.logger.info(f"Received message from client {client_id}: {data.get('type', 'unknown_type')}")
                    
                    # Process different message types
                    if data.get('type') == 'user_interaction':
                        await self.process_user_interaction(data, websocket)
                    elif data.get('type') == 'context_update':
                        # Update our context data
                        new_context = data.get('payload', {})
                        self.context_data.update(new_context)
                        self.logger.info("Context data updated")
                        
                        # If we have a memory system, update context there too
                        if self.memory_system:
                            try:
                                # Determine sensor type from the context data
                                sensor_type = new_context.get('sensor_type', 'unknown')
                                sensor_data = new_context.get('data', {})
                                
                                if sensor_type and sensor_data:
                                    await self.memory_system.process_sensor_data(sensor_type, sensor_data)
                                    self.logger.info(f"Updated memory system with context data for sensor: {sensor_type}")
                            except Exception as e:
                                self.logger.error(f"Error updating memory system with context: {e}")
                        
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
                            self.context_data[sensor_type] = sensor_data
                        
                        # If we have a memory system, process the sensor data
                        if self.memory_system and sensor_type:
                            try:
                                await self.memory_system.process_sensor_data(sensor_type, sensor_data)
                                self.logger.info(f"Processed {sensor_type} sensor data in memory system")
                            except Exception as e:
                                self.logger.error(f"Error processing sensor data in memory: {e}")
                        
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
                        
                        if self.memory_system and query:
                            try:
                                results = await self.memory_system.search_memory(query, limit)
                                await websocket.send(json.dumps({
                                    "type": "memory_query_results",
                                    "payload": {
                                        "query": query,
                                        "results": results,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }))
                                self.logger.info(f"Sent memory query results for: {query}")
                            except Exception as e:
                                self.logger.error(f"Error searching memory: {e}")
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
                            "memory_system_active": self.memory_system is not None,
                            "advanced_llm_initialized": self.llm_client is not None,
                            "llm_model": "llava" if self.llm_client else None,
                            "connected_clients": len(self.connected_clients),
                            "context_data_size": len(str(self.context_data)),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps({
                            "type": "status_response",
                            "payload": status_data
                        }))
                        self.logger.info("Sent status information")
                    else:
                        # Echo back with timestamp for other message types
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }))
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    self.logger.error(f"Error processing message from client {client_id}: {e}")
                    self.logger.error(traceback.format_exc())
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Error processing message: {str(e)}"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            self.logger.error(f"Error with client {client_id}: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
    
    async def broadcast_status(self):
        """Periodically broadcast status updates to all clients."""
        while True:
            if self.connected_clients:
                # Get memory system metrics if available
                memory_metrics = {}
                if self.memory_system:
                    try:
                        process = psutil.Process()
                        memory_info = process.memory_info()
                        memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                        
                        memory_metrics = {
                            "memory_system_active": True,
                            "memory_usage_mb": round(memory_usage_mb, 2),
                            "conversation_length": len(self.memory_system.conversation_memory.messages) if hasattr(self.memory_system, 'conversation_memory') else 0,
                            "context_entries": len(self.memory_system.context_memory.context_history) if hasattr(self.memory_system, 'context_memory') else 0
                        }
                    except Exception as e:
                        self.logger.error(f"Error getting memory metrics: {e}")
                        memory_metrics = {"memory_system_active": True, "error": str(e)}
                else:
                    memory_metrics = {"memory_system_active": False}
                
                # Create status message
                message = json.dumps({
                    "type": "status_update",
                    "data": {
                        "client_count": len(self.connected_clients),
                        "memory_system": memory_metrics,
                        "advanced_llm_initialized": self.llm_client is not None,
                        "llm_model": "llava" if self.llm_client else None,
                        "context_data_size": len(str(self.context_data)),
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                # Broadcast to all clients
                await asyncio.gather(
                    *[client.send(message) for client in self.connected_clients],
                    return_exceptions=True
                )
            
            await asyncio.sleep(10)
    
    def is_port_in_use(self, port):
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    
    async def start(self):
        """Start the WebSocket server."""
        try:
            # Check if port is in use
            if self.is_port_in_use(self.port):
                self.logger.error(f"Port {self.port} is already in use")
                
                # Try to forcefully release the port by killing any process using it
                os.system(f"lsof -ti :{self.port} | xargs kill -9 2>/dev/null || true")
                os.system(f"pkill -f 'port {self.port}' 2>/dev/null || true")
                
                # Wait a moment for the port to be released
                await asyncio.sleep(1)
                
                # Check again
                if self.is_port_in_use(self.port):
                    self.logger.error("Failed to release port")
                    return False
            
            # Initialize memory system
            self.logger.info("Initializing memory system...")
            memory_initialized = await self.initialize_memory_system()
            if memory_initialized:
                self.logger.info("Memory system initialized successfully")
            else:
                self.logger.warning("Memory system initialization failed, will use fallback responses")
                
            # Initialize advanced LLM service
            self.logger.info("Initializing advanced LLM service...")
            llm_initialized = await self.initialize_llm_service()
            if llm_initialized:
                self.logger.info("Advanced LLM service initialized successfully")
            else:
                self.logger.warning("Advanced LLM service initialization failed, will use fallback responses")
                    
            # Create the server
            server = await websockets.serve(
                self.handler,
                self.host,
                self.port,
                ping_interval=10,
                ping_timeout=5
            )
            
            self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            self.logger.info(f"Memory system: {'ACTIVE' if self.memory_system else 'INACTIVE'}")
            self.logger.info(f"Advanced LLM service: {'INITIALIZED' if self.llm_client else 'NOT AVAILABLE'}")
            
            # Save PID to file
            with open('pids/ws_server_8765.pid', 'w') as f:
                f.write(str(os.getpid()))
            
            # Start broadcast task
            broadcast_task = asyncio.create_task(self.broadcast_status())
            
            return True
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            self.logger.error(traceback.format_exc())
            return False

# Entry point for direct execution
async def start_server():
    """Start the WebSocket server with LLM integration."""
    server = LLMWebSocketServer()
    success = await server.start()
    if success:
        # Keep the server running indefinitely
        await asyncio.Future()

# This function is called from start_optimized_system_fixed.sh
def run_as_module():
    """Run the server as a module from start_optimized_system_fixed.sh."""
    asyncio.run(start_server())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
        sys.exit(1)