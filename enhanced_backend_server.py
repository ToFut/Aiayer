#!/usr/bin/env python3
"""
Enhanced Backend Server for WebSocket Communication
- Frontend communicates with this server on port 8765
- This server manages requests, interfaces with LocalLLM, and returns responses
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
import time

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create a custom filter to prevent duplicate logs
class DuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log = None
        self.last_time = None
        self.min_interval = 30  # Minimum seconds between similar logs
        self.connection_logs = set()  # Track unique connections
        self.error_counts = {}  # Track error frequencies

    def filter(self, record):
        # Skip connection logs for already logged connections
        if "WebSocket connection established" in record.getMessage():
            client_id = record.getMessage().split("from ")[-1]
            if client_id in self.connection_logs:
                return False
            self.connection_logs.add(client_id)
            return True

        # Handle connection errors with rate limiting
        if "Error initializing LLM service" in record.getMessage():
            error_key = "llm_init_error"
            current_time = time.time()
            
            if error_key not in self.error_counts:
                self.error_counts[error_key] = {"count": 0, "last_time": current_time}
            
            # Only log every 5 minutes if it's the same error
            if current_time - self.error_counts[error_key]["last_time"] < 300:
                self.error_counts[error_key]["count"] += 1
                return False
            
            self.error_counts[error_key] = {"count": 1, "last_time": current_time}
            return True

        # Handle other logs
        current_log = (record.levelno, record.getMessage())
        current_time = time.time()
        
        if current_log != self.last_log:
            self.last_log = current_log
            self.last_time = current_time
            return True
            
        if current_time - self.last_time >= self.min_interval:
            self.last_time = current_time
            return True
            
        return False

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/backend_server.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=2
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_backend')
logger.addFilter(DuplicateFilter())

# Reduce logging level for all modules
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('uvicorn').setLevel(logging.ERROR)
logging.getLogger('fastapi').setLevel(logging.ERROR)
logging.getLogger('psutil').setLevel(logging.ERROR)

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
        
        # Check if memory system module exists
        memory_system_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "memory/memory_system.py")
        if not os.path.exists(memory_system_path):
            logger.warning(f"Memory system module not found at {memory_system_path}")
            logger.info("Attempting to use minimal_memory as fallback...")
            
            # Try to import minimal memory implementation as fallback
            try:
                minimal_memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "utils/minimal_memory.py")
                if os.path.exists(minimal_memory_path):
                    spec = importlib.util.spec_from_file_location(
                        "minimal_memory", minimal_memory_path
                    )
                    memory_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(memory_module)
                    
                    # Initialize minimal memory system
                    memory_system = memory_module.MinimalMemory()
                    await memory_system.initialize()
                    
                    logger.info("Minimal memory system initialized successfully as fallback")
                    return True
                else:
                    logger.warning("Minimal memory fallback not found, continuing without memory system")
                    return False
            except Exception as fallback_e:
                logger.error(f"Error initializing minimal memory fallback: {fallback_e}")
                logger.error(traceback.format_exc())
                return False
        
        # Dynamically import memory system
        spec = importlib.util.spec_from_file_location(
            "memory_system", memory_system_path
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
        
        # Attempt to use in-memory dictionary as minimal fallback
        try:
            logger.info("Attempting to create simple in-memory fallback...")
            
            # Create a minimal memory class on the fly
            class SimpleMemoryFallback:
                def __init__(self):
                    self.memory_dict = {}
                    self.conversation_memory = type('obj', (object,), {'messages': []})
                    self.context_memory = type('obj', (object,), {'context_history': []})
                
                async def initialize(self):
                    return True
                
                async def add_message(self, message):
                    if 'messages' not in self.memory_dict:
                        self.memory_dict['messages'] = []
                    self.memory_dict['messages'].append(message)
                    self.conversation_memory.messages = self.memory_dict['messages']
                    return True
                
                async def get_context_summary(self):
                    return {}
                
                async def search_memory(self, query, limit=3):
                    return []
                
                async def process_sensor_data(self, sensor_type, data):
                    if 'sensor_data' not in self.memory_dict:
                        self.memory_dict['sensor_data'] = {}
                    self.memory_dict['sensor_data'][sensor_type] = data
                    return True
            
            memory_system = SimpleMemoryFallback()
            await memory_system.initialize()
            logger.info("Simple in-memory fallback initialized")
            return True
            
        except Exception as fallback_e:
            logger.error(f"Failed to create simple memory fallback: {fallback_e}")
            return False

async def initialize_llm_service():
    """Initialize connection to the self-contained LLM service."""
    global llm_client
    
    try:
        logger.info("Initializing connection to self-contained LLM service...")
        
        # Create a WebSocket client for the LLM service
        class LLMWebSocketClient:
            def __init__(self):
                self.websocket = None
                self.is_initialized = False
                self.url = "ws://localhost:8766"
                self.retry_count = 0
                self.max_retries = 3
            
            async def initialize(self):
                if self.retry_count >= self.max_retries:
                    return False
                    
                self.retry_count += 1
                
                try:
                    # Close existing connection if any
                    if self.websocket:
                        try:
                            await self.websocket.close()
                        except:
                            pass
                        self.websocket = None
                    
                    # Create new connection with basic configuration
                    self.websocket = await websockets.connect(
                        self.url,
                        ping_interval=None,
                        ping_timeout=None,
                        close_timeout=1,
                        max_size=1024*1024,
                        compression=None
                    )
                    
                    # Wait for welcome message
                    response = await self.websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "welcome":
                        self.is_initialized = True
                        self.retry_count = 0
                        return True
                    return False
                    
                except Exception as e:
                    logger.error(f"Failed to connect to LLM service: {str(e)}")
                    return False
            
            async def generate_response(self, messages):
                if not self.is_initialized:
                    success = await self.initialize()
                    if not success:
                        return "LLM service is currently unavailable. Please try again later."
                
                try:
                    # Format the message for the LLM service
                    query = messages[-1]["content"] if isinstance(messages, list) else str(messages)
                    
                    # Send request
                    await self.websocket.send(json.dumps({
                        "type": "llm_request",
                        "payload": {
                            "message": query
                        }
                    }))
                    
                    # Get response
                    response = await self.websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "llm_response":
                        return response_data.get("content", "No response generated")
                    else:
                        self.is_initialized = False
                        return "Error: Unexpected response from LLM service"
                        
                except Exception as e:
                    self.is_initialized = False
                    return f"Error: {str(e)}"
            
            async def close(self):
                """Properly close the WebSocket connection"""
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except:
                        pass
                    self.websocket = None
                self.is_initialized = False
        
        llm_client = LLMWebSocketClient()
        success = await llm_client.initialize()
        
        if success:
            logger.info("Successfully initialized connection to self-contained LLM service")
            return True
        else:
            logger.error("Failed to initialize connection to self-contained LLM service")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing LLM service connection: {e}")
        logger.error(traceback.format_exc())
        return False

async def call_local_llm(query, context=None):
    """Call the LocalLLM directly with the user query and context."""
    global llm_client
    
    # Maximum retries for LLM call
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            if not llm_client:
                logger.error("LocalLLM not initialized")
                return "I'm currently operating in a limited capacity. Your query couldn't be processed by the LLM service."
            
            if not hasattr(llm_client, 'generate_response'):
                logger.error("LocalLLM missing generate_response method")
                return "The LLM service is missing the required generate_response method. I'm operating in fallback mode."
            
            # Format messages for the LocalLLM format (which uses the OpenAI-style format)
            system_message = """You are a helpful assistant with access to the user's screen content and active applications. 
Use this context to provide more helpful responses. Your responses should be informed by both the current context and relevant past interactions."""

            # Add context to system message in a structured format
            if context:
                system_message += "\n\nCurrent Context:"
                
                # Add current environment information
                if isinstance(context, dict):
                    # Current window and applications
                    if 'window' in context:
                        system_message += f"\n- Active Window: {context.get('window', 'Unknown')}"
                    if 'active_apps' in context:
                        apps = context.get('active_apps', [])
                        if isinstance(apps, list):
                            apps = [str(app) for app in apps]
                        system_message += f"\n- Active Applications: {', '.join(apps)}"
                    
                    # Screen content
                    if 'screen_content' in context:
                        screen_content = context.get('screen_content', '')
                        shortened = screen_content[:500] + "..." if len(screen_content) > 500 else screen_content
                        system_message += f"\n- Screen Content: {shortened}"
                    
                    # Current file information
                    if 'current_file' in context:
                        file_info = context.get('current_file', {})
                        if isinstance(file_info, dict):
                            system_message += f"\n- Current File: {file_info.get('path', 'Unknown')}"
                            if 'type' in file_info:
                                system_message += f" (Type: {file_info['type']})"
                    
                    # Recent files
                    if 'recent_files' in context:
                        recent_files = context.get('recent_files', [])
                        if recent_files:
                            system_message += "\n- Recent Files:"
                            for file in recent_files[:3]:  # Show only 3 most recent
                                system_message += f"\n  * {file}"
                    
                    # Add relevant memories with proper formatting
                    if 'relevant_memories' in context:
                        memories = context.get('relevant_memories', [])
                        if memories:
                            system_message += "\n\nRelevant Past Information:"
                            for i, memory in enumerate(memories, 1):
                                if isinstance(memory, dict):
                                    content = memory.get('content', '')
                                    score = memory.get('_search_score', 0)
                                    source = memory.get('_search_source', 'unknown')
                                    if content:
                                        system_message += f"\n{i}. {content}"
                                        system_message += f"\n   (Relevance: {score:.2f}, Source: {source})"
                    
                    # Add any additional context
                    additional_context = {k: v for k, v in context.items() 
                                       if k not in ['window', 'active_apps', 'screen_content', 
                                                  'current_file', 'recent_files', 'relevant_memories']}
                    if additional_context:
                        system_message += "\n\nAdditional Context:"
                        for key, value in additional_context.items():
                            if isinstance(value, (str, int, float, bool)):
                                system_message += f"\n- {key}: {value}"
            
            # Prepare messages in the format expected by the LocalLLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ]
            
            # Call the LocalLLM generate_response method
            logger.info(f"Calling local LLM with user query (retry {retry_count}/{max_retries})")
            response_text = await llm_client.generate_response(messages)
            
            # Validate response
            if not response_text or response_text.strip() == "":
                raise ValueError("Empty response received from LLM")
            
            logger.info(f"LocalLLM returned response: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling LocalLLM (retry {retry_count}/{max_retries}): {e}")
            logger.error(traceback.format_exc())
            retry_count += 1
            
            # If we still have retries, wait briefly and continue
            if retry_count <= max_retries:
                logger.info(f"Retrying LLM call in 1 second... (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(1)
            else:
                # If we've exhausted retries, return fallback response
                logger.warning(f"Exhausted all {max_retries} retries for LLM call")
                return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

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
        
        # Combine the provided context with memory context
        combined_context = {}
        if context:
            combined_context.update(context)
        if memory_context:
            combined_context.update(memory_context)
            
        # Call the LocalLLM with the combined context
        if llm_client:
            response_text = await call_local_llm(query, combined_context)
            
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
                    "context_used": bool(combined_context),
                    "memory_used": bool(memory_context),
                    "advanced_llm": True
                }
            }
            
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
            "how does this work": [
                "This system monitors your environment through sensors that track your screen content and running applications. It then uses this context to provide more relevant assistance.",
                "The system uses various sensors to understand your work context, including what's on your screen and which applications you're using. This helps me provide more personalized responses.",
                "I work by collecting contextual information about your activities, which helps me understand what you're working on and provide more relevant assistance."
            ],
            "now": [
                "I'm ready to assist you with your current tasks. What specifically would you like help with?",
                "Now that the system is running, I can provide assistance based on your current work context. How can I help?",
                "I'm actively monitoring your work environment and ready to provide assistance. What would you like to know?"
            ],
            "hey": [
                "Hello! I'm here to assist you. What can I help with today?",
                "Hi there! I'm ready to help with your questions or tasks.",
                "Greetings! How can I assist you with your current activities?"
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

async def handler(websocket):
    """Handle WebSocket connections and messages."""
    global connected_clients, memory_system, llm_client
    
    client_id = id(websocket)
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "status": "connected"
            }
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type', 'unknown')
                logger.info(f"Received message from client {client_id}: {message_type}")
                
                if message_type == 'llm_request':
                    # Process LLM request
                    query = data.get('payload', {}).get('query', '')
                    if not query:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "No query provided in request",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        continue
                        
                    # Generate response
                    response = await generate_response(query, data.get('payload', {}).get('context'))
                    if response:
                        try:
                            await websocket.send(json.dumps(response))
                        except websockets.exceptions.ConnectionClosed:
                            logger.info(f"Client {client_id} disconnected during response")
                            break
                            
                elif message_type == 'context_request':
                    # Send current context
                    try:
                        context_summary = {}
                        if memory_system:
                            try:
                                context_summary = await memory_system.get_context_summary()
                            except Exception as mem_ex:
                                logger.error(f"Error getting context summary: {mem_ex}")
                                context_summary = {"error": "Failed to retrieve context"}
                                
                        await websocket.send(json.dumps({
                            "type": "context_update",
                            "payload": {
                                "context": context_summary,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    except Exception as e:
                        logger.error(f"Error sending context: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Failed to retrieve context",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        
                elif message_type == 'status_request':
                    # Send current status
                    try:
                        status_data = {
                            "client_count": len(connected_clients),
                            "memory_system": {
                                "active": memory_system is not None,
                                "error": None
                            },
                            "llm_service": {
                                "active": llm_client is not None,
                                "model": getattr(llm_client, 'model_name', None) if llm_client else None
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps({
                            "type": "status_response",
                            "payload": status_data
                        }))
                    except Exception as e:
                        logger.error(f"Error sending status: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Failed to retrieve status",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                else:
                    # Echo back with timestamp for other message types
                    try:
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "payload": {
                                "data": data,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    except websockets.exceptions.ConnectionClosed:
                        logger.info(f"Client {client_id} disconnected during echo")
                        break
                        
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                try:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Client {client_id} disconnected after JSON error")
                    break
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                logger.error(traceback.format_exc())
                try:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": f"Error processing message: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Client {client_id} disconnected after error")
                    break
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            logger.info(f"Removed client {client_id} from connected clients")

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    global memory_system, llm_client
    
    while True:
        if connected_clients:
            # Get memory system metrics if available
            memory_metrics = {"memory_system_active": False}
            
            if memory_system:
                try:
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                    
                    # Get conversation count safely based on the type of memory system
                    conversation_count = 0
                    try:
                        # First try memory_dict for SimpleMemoryFallback
                        if hasattr(memory_system, 'memory_dict') and isinstance(memory_system.memory_dict, dict):
                            messages = memory_system.memory_dict.get('messages', [])
                            if isinstance(messages, list):
                                conversation_count = len(messages)
                        # Then try conversation_memory for regular MemorySystem
                        elif hasattr(memory_system, 'conversation_memory'):
                            if hasattr(memory_system.conversation_memory, 'messages'):
                                if isinstance(memory_system.conversation_memory.messages, list):
                                    conversation_count = len(memory_system.conversation_memory.messages)
                    except Exception as detail_error:
                        logger.error(f"Error getting conversation count: {detail_error}")
                    
                    # Simplified and safer memory metrics
                    memory_metrics = {
                        "memory_system_active": True,
                        "memory_usage_mb": round(memory_usage_mb, 2),
                        "conversation_length": conversation_count,
                        "context_entries": 0  # Simplified 
                    }
                except Exception as e:
                    logger.error(f"Error getting memory metrics: {e}")
                    memory_metrics = {"memory_system_active": True, "error": str(e)}
            
            # Create status message
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "memory_system": memory_metrics,
                    "advanced_llm_initialized": llm_client is not None,
                    "llm_model": getattr(llm_client, 'model_name', None) if llm_client else None,
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
        
        # Ensure necessary directories exist
        for directory in ['logs', 'pids', 'cache']:
            os.makedirs(directory, exist_ok=True)
        
        # Use port 8765 to match the Tauri app's expectation
        port = 8765
        
        # Check if port is in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            
            # Try to forcefully release the port by killing any process using it
            try:
                os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
                os.system(f"pkill -f 'port {port}' 2>/dev/null || true")
                
                # Wait a moment for the port to be released
                await asyncio.sleep(1)
                
                # Check again
                if is_port_in_use(port):
                    logger.error("Failed to release port")
                    sys.exit(1)
            except Exception as port_ex:
                logger.error(f"Error while trying to release port: {port_ex}")
                sys.exit(1)
        
        # Initialize memory system
        logger.info("Initializing memory system...")
        memory_initialized = await initialize_memory_system()
        
        # Initialize LLM service
        logger.info("Initializing LLM service...")
        llm_initialized = await initialize_llm_service()
        
        # Create the server with basic configuration
        try:
            server = await websockets.serve(
                handler,
                "0.0.0.0",
                port,
                ping_interval=None,
                ping_timeout=None,
                close_timeout=1,
                max_size=1024*1024,
                compression=None
            )
            
            logger.info(f"Backend server started on ws://0.0.0.0:{port}")
            
            # Save PID to file
            try:
                with open('pids/backend_server.pid', 'w') as f:
                    f.write(str(os.getpid()))
            except Exception as pid_ex:
                logger.error(f"Failed to write PID file: {pid_ex}")
            
            # Start broadcast task
            broadcast_task = asyncio.create_task(broadcast_status())
            
            # Keep the server running
            await server.wait_closed()
            
        except Exception as server_ex:
            logger.error(f"Error starting WebSocket server: {server_ex}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error starting server: {e}")
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