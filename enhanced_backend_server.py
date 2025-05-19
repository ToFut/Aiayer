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

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend_server.log'),
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
    """Initialize the advanced LLM service using the LocalLLM implementation."""
    global llm_client
    
    llm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm/model.py")
    
    # Try primary LLM implementation
    try:
        # Check if LLM module exists
        if not os.path.exists(llm_path):
            logger.warning(f"LLM module not found at {llm_path}")
            raise FileNotFoundError(f"LLM module not found at {llm_path}")
        
        # Import the LocalLLM class
        logger.info("Initializing advanced LLM service...")
        
        # Dynamically import LocalLLM
        spec = importlib.util.spec_from_file_location("model", llm_path)
        llm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_module)
        
        # Initialize the LocalLLM instance (try llava first)
        try:
            llm_client = llm_module.LocalLLM(model_name="llava")
            logger.info("Checking llava model availability...")
            await llm_client.initialize()
            logger.info("Advanced LLM service initialized successfully with llava")
            return True
        except Exception as llava_e:
            logger.warning(f"Failed to initialize llava model: {llava_e}")
            logger.info("Trying mistral model as fallback...")
            
            # Try with mistral as fallback
            try:
                llm_client = llm_module.LocalLLM(model_name="mistral")
                await llm_client.initialize()
                logger.info("Advanced LLM service initialized with mistral fallback")
                return True
            except Exception as mistral_e:
                logger.warning(f"Failed to initialize mistral model: {mistral_e}")
                raise mistral_e
                
    except Exception as e:
        logger.error(f"Error initializing advanced LLM service: {e}")
        logger.error(traceback.format_exc())
        
        # Try simplified mock LLM as fallback
        try:
            logger.info("Creating simplified mock LLM as ultimate fallback...")
            
            # Create a minimal LLM class on the fly with basic features
            class MockLLM:
                def __init__(self, model_name="mock"):
                    self.model_name = model_name
                    self.is_initialized = False
                    self.response_templates = [
                        "Based on your query about '{topic}', I can provide this information: {detail}",
                        "Regarding '{topic}', here's what I found: {detail}",
                        "I've analyzed your question about '{topic}'. {detail}",
                        "Here's my response about '{topic}': {detail}"
                    ]
                    self.knowledge_base = {
                        "help": "I can assist with analyzing your environment, answering questions, and providing contextual information.",
                        "system": "I'm a simplified assistant operating in fallback mode. Some advanced features may be unavailable.",
                        "context": "I can work with basic context information from your environment.",
                        "default": "While I'm operating in a limited mode, I'll do my best to assist you with basic information."
                    }
                
                async def initialize(self):
                    self.is_initialized = True
                    return True
                
                async def generate_response(self, messages):
                    """Generate a response based on the input messages"""
                    import random
                    
                    # Extract query from messages
                    query = ""
                    if isinstance(messages, list) and len(messages) > 0:
                        for msg in messages:
                            if msg.get("role") == "user":
                                query = msg.get("content", "")
                                break
                    
                    # Fall back to last message if no user message found
                    if not query and len(messages) > 0:
                        query = messages[-1].get("content", "")
                    
                    # Generate a topic from the query
                    query_words = query.split()
                    topic = query
                    if len(query_words) > 5:
                        topic = " ".join(query_words[:5]) + "..."
                    
                    # Find relevant detail from knowledge base or use default
                    detail = self.knowledge_base.get("default")
                    for key, value in self.knowledge_base.items():
                        if key in query.lower():
                            detail = value
                            break
                    
                    # Format the response
                    template = random.choice(self.response_templates)
                    response = template.format(topic=topic, detail=detail)
                    
                    return response
            
            # Initialize mock LLM
            llm_client = MockLLM()
            await llm_client.initialize()
            logger.info("Mock LLM initialized as fallback")
            return True
            
        except Exception as fallback_e:
            logger.error(f"Failed to create mock LLM fallback: {fallback_e}")
            llm_client = None
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
            system_message = "You are a helpful assistant with access to the user's screen content and active applications. Use this context to provide more helpful responses."
            
            # Add context to system message
            if context:
                system_message += "\n\nContext:"
                if isinstance(context, dict):
                    if 'window' in context:
                        system_message += f"\nActive Window: {context.get('window', 'Unknown')}"
                    if 'active_apps' in context:
                        system_message += f"\nActive Applications: {', '.join(context.get('active_apps', []))}"
                    if 'screen_content' in context:
                        screen_content = context.get('screen_content', '')
                        shortened = screen_content[:500] + "..." if len(screen_content) > 500 else screen_content
                        system_message += f"\nScreen Content: {shortened}"
                    if 'relevant_memories' in context:
                        system_message += "\nRelevant Past Information:"
                        for i, memory in enumerate(context['relevant_memories']):
                            system_message += f"\n - {memory.get('content', 'No content')}"
            
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
                
                # Generate a fallback response based on the query
                import random
                
                # Predefined response templates for fallback
                fallback_templates = [
                    "I'm sorry, but I encountered an issue while processing your query about '{topic}'. {detail}",
                    "Due to a technical limitation, I couldn't fully process your question about '{topic}'. {detail}",
                    "While I'd like to help with your question about '{topic}', I'm currently experiencing a technical issue. {detail}",
                    "Your query about '{topic}' is important, but I'm having trouble providing a complete answer right now. {detail}"
                ]
                
                fallback_details = [
                    "I'm operating in a fallback mode with limited capabilities at the moment.",
                    "The advanced language model is currently unavailable, but I'll try to assist with basic information.",
                    "My normal language processing capabilities are temporarily limited.",
                    "I'm using a simplified response system while the main system is unavailable."
                ]
                
                # Extract topic from query (first few words)
                query_words = query.split()
                topic = query if len(query_words) <= 5 else " ".join(query_words[:5]) + "..."
                
                # Format fallback response
                template = random.choice(fallback_templates)
                detail = random.choice(fallback_details)
                fallback_response = template.format(topic=topic, detail=detail)
                
                return fallback_response

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
            memory_metrics = {}
            if memory_system:
                try:
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                    
                    # Safely get memory metrics
                    memory_metrics = {
                        "memory_system_active": True,
                        "memory_usage_mb": round(memory_usage_mb, 2),
                        "conversation_length": len(getattr(memory_system, 'conversation_memory', {}).get('messages', [])) if hasattr(memory_system, 'conversation_memory') else 0,
                        "context_entries": len(getattr(memory_system, 'context_memory', {}).get('context_history', [])) if hasattr(memory_system, 'context_memory') else 0
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
                    
                    # Try alternate port as fallback
                    alternate_port = 8766
                    logger.info(f"Trying alternate port {alternate_port} as fallback")
                    
                    if not is_port_in_use(alternate_port):
                        port = alternate_port
                        logger.info(f"Using alternate port {port}")
                    else:
                        logger.error(f"Alternate port {alternate_port} also in use, server cannot start")
                        sys.exit(1)
            except Exception as port_ex:
                logger.error(f"Error while trying to release port: {port_ex}")
                logger.error(traceback.format_exc())
                # Try alternate port
                alternate_port = 8766
                if not is_port_in_use(alternate_port):
                    port = alternate_port
                    logger.info(f"Using alternate port {port}")
                else:
                    logger.error(f"Alternate port {alternate_port} also in use, server cannot start")
                    sys.exit(1)
        
        # Initialize memory system with retry logic
        logger.info("Initializing memory system...")
        max_memory_retries = 2
        memory_retry_count = 0
        memory_initialized = False
        
        while not memory_initialized and memory_retry_count <= max_memory_retries:
            memory_initialized = await initialize_memory_system()
            if memory_initialized:
                logger.info("Memory system initialized successfully")
                break
            
            memory_retry_count += 1
            if memory_retry_count <= max_memory_retries:
                logger.warning(f"Memory system initialization failed (attempt {memory_retry_count}/{max_memory_retries}), retrying in 2 seconds...")
                await asyncio.sleep(2)
        
        if not memory_initialized:
            logger.warning(f"Memory system initialization failed after {max_memory_retries} attempts, will use simplified fallback")
            
        # Initialize advanced LLM service with retry logic
        logger.info("Initializing advanced LLM service...")
        max_llm_retries = 2
        llm_retry_count = 0
        llm_initialized = False
        
        while not llm_initialized and llm_retry_count <= max_llm_retries:
            llm_initialized = await initialize_llm_service()
            if llm_initialized:
                logger.info("Advanced LLM service initialized successfully")
                break
            
            llm_retry_count += 1
            if llm_retry_count <= max_llm_retries:
                logger.warning(f"LLM service initialization failed (attempt {llm_retry_count}/{max_llm_retries}), retrying in 2 seconds...")
                await asyncio.sleep(2)
        
        if not llm_initialized:
            logger.warning(f"LLM service initialization failed after {max_llm_retries} attempts, will use rule-based fallback responses")
                
        # Create the server with error handling
        try:
            server = await websockets.serve(
                handler,
                "0.0.0.0",  # Bind to all interfaces
                port,
                ping_interval=10,
                ping_timeout=5
            )
            
            logger.info(f"Backend server started on ws://0.0.0.0:{port}")
            logger.info(f"Memory system: {'ACTIVE' if memory_system else 'INACTIVE'}")
            logger.info(f"Advanced LLM service: {'INITIALIZED' if llm_client else 'NOT AVAILABLE'}")
            
            # Save PID to file
            try:
                with open('pids/backend_server.pid', 'w') as f:
                    f.write(str(os.getpid()))
            except Exception as pid_ex:
                logger.error(f"Failed to write PID file: {pid_ex}")
            
            # Record server status to a status file for monitoring
            try:
                status_data = {
                    "server": "enhanced_backend_server",
                    "status": "running",
                    "port": port,
                    "pid": os.getpid(),
                    "memory_system": memory_initialized,
                    "llm_service": llm_initialized,
                    "llm_model": llm_client.model_name if llm_client else "none",
                    "start_time": datetime.now().isoformat()
                }
                
                with open('logs/server_status.json', 'w') as f:
                    json.dump(status_data, f, indent=2)
            except Exception as status_ex:
                logger.error(f"Failed to write status file: {status_ex}")
            
            # Start broadcast task with error handling
            try:
                broadcast_task = asyncio.create_task(broadcast_status())
                broadcast_task.add_done_callback(
                    lambda task: logger.error(f"Broadcast task ended: {task.exception()}") if task.exception() else None
                )
            except Exception as broadcast_ex:
                logger.error(f"Failed to start broadcast task: {broadcast_ex}")
            
            # Keep the server running
            await asyncio.Future()
            
        except Exception as server_ex:
            logger.error(f"Error starting WebSocket server: {server_ex}")
            logger.error(traceback.format_exc())
            
            # Try starting with simpler configuration as last resort
            try:
                logger.info("Attempting to start server with minimal configuration as last resort")
                basic_server = await websockets.serve(
                    handler,
                    "localhost",  # Only bind to localhost as fallback
                    port,
                    ping_interval=None,  # Disable ping/pong to reduce complexity
                    ping_timeout=None
                )
                
                logger.info(f"Basic server started on ws://localhost:{port} (limited functionality)")
                await asyncio.Future()
            except Exception as basic_ex:
                logger.error(f"Failed to start even basic server: {basic_ex}")
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error starting server: {e}")
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