#!/usr/bin/env python3
"""
Agent-Based WebSocket Server with LocalLLM Integration
This script implements an agent-based architecture that mediates between clients,
memory system, and LLM service for more intelligent and context-aware responses.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import aiohttp
import importlib.util
import traceback
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_based_llm_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent_based_llm')

# WebSocket clients
connected_clients = set()
client_info = {}  # Store client info by ID

# Global components
memory_system = None
ollama_service = None

class OllamaService:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3"  # Default model, will try to find best available
        
    async def list_models(self):
        """List available models from Ollama API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        models = await resp.json()
                        logger.info(f"Available Ollama models: {models}")
                        
                        # Find a model to use
                        if models and "models" in models and models["models"]:
                            # Try to find a good model or default to first available
                            for model in models["models"]:
                                # Prefer llama3 models
                                if "llama3" in model["name"].lower():
                                    self.model_name = model["name"]
                                    logger.info(f"Using model: {self.model_name}")
                                    return True
                                # Fallback to any llama model
                                elif "llama" in model["name"].lower():
                                    self.model_name = model["name"]
                                    logger.info(f"Using model: {self.model_name}")
                                    return True
                            
                            # If no preferred model found, use first available
                            self.model_name = models["models"][0]["name"]
                            logger.info(f"Using model: {self.model_name}")
                            return True
                        
                        logger.warning("No Ollama models found")
                        return False
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return False
        
    async def generate_response(self, prompt):
        """Generate a response using Ollama API"""
        try:
            logger.info(f"Generating response with prompt length: {len(prompt)}")
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                start_time = datetime.now()
                logger.info(f"Calling Ollama API at {self.ollama_url}/api/generate")
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return {
                            "response": f"Error generating response: {resp.status} - {error_text}",
                            "model": self.model_name,
                            "error": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    result = await resp.json()
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Generated response in {processing_time:.2f}s")
                    logger.info(f"Response: {result.get('response', '')[:100]}...")
                    
                    return {
                        "response": result.get("response", "No response generated"),
                        "model": self.model_name,
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": f"Sorry, I encountered an error while generating a response: {str(e)}",
                "model": self.model_name,
                "error": True,
                "timestamp": datetime.now().isoformat()
            }

class Agent:
    """Intelligent agent that mediates between clients, memory, and LLM"""
    
    def __init__(self, memory_system=None, llm_service=None):
        self.memory_system = memory_system
        self.llm_service = llm_service
        self.logger = logging.getLogger('agent')
        self.conversation_history = []  # Maintain local conversation history
        
    async def process_message(self, user_message, client_id=None):
        """Process a user message, collect context, and generate a response"""
        try:
            self.logger.info(f"Agent processing message from client {client_id}")
            
            # 1. Store user message in conversation history and memory system
            timestamp = datetime.now().isoformat()
            message_data = {
                "type": "user_message", 
                "content": user_message,
                "client_id": client_id,
                "timestamp": timestamp
            }
            
            self.conversation_history.append(message_data)
            
            # Store in memory system if available
            if self.memory_system:
                try:
                    await self.memory_system.add_message(message_data)
                    self.logger.info("Stored user message in memory system")
                except Exception as e:
                    self.logger.error(f"Error storing message in memory: {e}")
            
            # 2. Collect relevant context from memory system
            context = await self.collect_context(user_message)
            
            # 3. Construct prompt for LLM with context
            prompt = await self.construct_prompt(user_message, context)
            
            # 4. Generate response using LLM service
            if self.llm_service:
                response_data = await self.llm_service.generate_response(prompt)
                response_text = response_data.get("response", "")
            else:
                response_text = "Agent could not connect to LLM service to generate a response."
                response_data = {
                    "response": response_text,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 5. Store response in conversation history and memory system
            response_message = {
                "type": "assistant_message",
                "content": response_text,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.conversation_history.append(response_message)
            
            # Store in memory system if available
            if self.memory_system:
                try:
                    await self.memory_system.add_message(response_message)
                    self.logger.info("Stored assistant response in memory system")
                except Exception as e:
                    self.logger.error(f"Error storing response in memory: {e}")
            
            # 6. Return response data
            return {
                **response_data,
                "context_used": bool(context),
                "agent_processed": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent processing: {e}")
            self.logger.error(traceback.format_exc())
            return {
                "response": f"The agent encountered an error while processing your message: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def collect_context(self, user_message):
        """Collect relevant context from memory system"""
        context = {}
        
        if not self.memory_system:
            self.logger.warning("No memory system available for context collection")
            return context
        
        try:
            # 1. Get current environment context
            try:
                context_summary = await self.memory_system.get_context_summary()
                self.logger.info(f"Retrieved context summary with {len(str(context_summary))} chars")
                context = context_summary
            except Exception as e:
                self.logger.error(f"Error getting context summary: {e}")
            
            # 2. Search for relevant memories related to the user's query
            try:
                relevant_memories = await self.memory_system.search_memory(user_message, limit=5)
                if relevant_memories:
                    self.logger.info(f"Found {len(relevant_memories)} relevant memories")
                    context['relevant_memories'] = relevant_memories
            except Exception as e:
                self.logger.error(f"Error searching memory: {e}")
            
            # 3. Get recent conversation history
            try:
                recent_messages = self.memory_system.get_recent_messages(count=5)
                if recent_messages:
                    self.logger.info(f"Retrieved {len(recent_messages)} recent messages")
                    context['recent_messages'] = recent_messages
            except Exception as e:
                self.logger.error(f"Error getting recent messages: {e}")
                # Fallback to local conversation history
                context['recent_messages'] = self.conversation_history[-5:] if len(self.conversation_history) > 0 else []
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error collecting context: {e}")
            self.logger.error(traceback.format_exc())
            return {}
    
    async def construct_prompt(self, user_message, context):
        """Construct an optimized prompt for the LLM with relevant context"""
        try:
            # Start with a system message
            system_message = "You are a helpful assistant with access to the user's environment context.\n\n"
            
            # Include relevant context information
            if context:
                # Add active window and application if available
                if 'window' in context:
                    system_message += f"Active Window: {context.get('window', 'Unknown')}\n"
                if 'active_apps' in context:
                    apps = context.get('active_apps', [])
                    if apps:
                        system_message += f"Active Applications: {', '.join(apps)}\n"
                
                # Add screen content if available (truncated to avoid overly long prompts)
                if 'screen_content' in context and context['screen_content']:
                    screen_content = context['screen_content']
                    # Truncate if needed
                    if len(screen_content) > 1000:
                        screen_content = screen_content[:1000] + "...(truncated)"
                    system_message += f"\nScreen Content:\n{screen_content}\n"
                
                # Add conversation history if available
                if 'recent_messages' in context and context['recent_messages']:
                    system_message += "\nRecent Conversation:\n"
                    for msg in context['recent_messages']:
                        if isinstance(msg, dict):
                            role = "User" if msg.get('type') == 'user_message' else "Assistant"
                            content = msg.get('content', '')
                            if content:
                                system_message += f"{role}: {content}\n"
                
                # Add relevant memories if available
                if 'relevant_memories' in context and context['relevant_memories']:
                    system_message += "\nRelevant Context From Memory:\n"
                    for i, memory in enumerate(context['relevant_memories']):
                        if isinstance(memory, dict) and 'content' in memory:
                            system_message += f"- {memory['content']}\n"
            
            # Add user's current message
            full_prompt = f"{system_message}\n\nUser: {user_message}\n\nAssistant:"
            
            self.logger.info(f"Constructed prompt with {len(full_prompt)} chars")
            return full_prompt
            
        except Exception as e:
            self.logger.error(f"Error constructing prompt: {e}")
            # Fallback to simple prompt
            return f"User: {user_message}\nAssistant:"
    
    async def process_sensor_data(self, sensor_type, sensor_data):
        """Process and store sensor data in memory system"""
        if not self.memory_system:
            self.logger.warning(f"No memory system available to process {sensor_type} sensor data")
            return False
        
        try:
            await self.memory_system.process_sensor_data(sensor_type, sensor_data)
            self.logger.info(f"Processed {sensor_type} sensor data")
            return True
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            return False
    
    async def search_memory(self, query, limit=5):
        """Search memory for relevant information"""
        if not self.memory_system:
            self.logger.warning("No memory system available for search")
            return []
        
        try:
            results = await self.memory_system.search_memory(query, limit)
            self.logger.info(f"Memory search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            self.logger.error(f"Error searching memory: {e}")
            return []

# Initialize agent
agent = None

# Extract message from different payload formats
def extract_message(data):
    """Extract the user message from different possible data formats"""
    if 'payload' in data and isinstance(data['payload'], dict):
        return data['payload'].get('message', data['payload'].get('query', ''))
    elif 'message' in data:
        return data['message']
    elif 'query' in data:
        return data['query']
    return ""

async def initialize_memory_system():
    """Initialize the memory system for context-aware responses"""
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
        return memory_system
    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        logger.error(traceback.format_exc())
        return None

# WebSocket handler
async def websocket_handler(websocket):
    """Handle WebSocket connections with agent mediation"""
    global agent
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    path = websocket.path if hasattr(websocket, 'path') else ""
    client_info[client_id] = {"type": "unknown", "connected_at": datetime.now().isoformat(), "path": path}
    logger.info(f"Client {client_id} connected on path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Agent-Based LLM WebSocket Server",
            "agent_active": agent is not None,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle connection establishment
                if msg_type == 'connection_established':
                    client_info[client_id]["type"] = data.get('payload', {}).get('client', 'unknown')
                    logger.info(f"Client {client_id} identified as: {client_info[client_id]['type']}")
                    
                    # Send ready confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "model": ollama_service.model_name if ollama_service else "unknown",
                            "agent_active": agent is not None,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Handle status request
                elif msg_type == 'status_request':
                    # Send status response
                    await websocket.send(json.dumps({
                        "type": "status_response",
                        "payload": {
                            "connected_clients": len(connected_clients),
                            "model": ollama_service.model_name if ollama_service else "unknown",
                            "agent_active": agent is not None,
                            "memory_active": agent.memory_system is not None if agent else False,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Handle context request
                elif msg_type == 'context_request':
                    # Get context from agent if available
                    context = {}
                    if agent and agent.memory_system:
                        try:
                            context = await agent.memory_system.get_context_summary()
                            logger.info(f"Retrieved context summary with {len(str(context))} chars")
                        except Exception as e:
                            logger.error(f"Error retrieving context summary: {e}")
                            context = {"error": str(e)}
                    
                    # Send context response
                    await websocket.send(json.dumps({
                        "type": "context_update",
                        "payload": {
                            "context": context,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Send a welcome message for better visibility
                    welcome_message = f"Hello! I'm your agent-based LLM assistant."
                    if agent and agent.memory_system:
                        welcome_message += " I can access your environment context and remember our conversation."
                    welcome_message += " What would you like to talk about?"
                    
                    await websocket.send(json.dumps({
                        "type": "llm_response",
                        "content": welcome_message,
                        "payload": {
                            "response": welcome_message,
                            "model": ollama_service.model_name if ollama_service else "unknown",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Handle sensor data
                elif msg_type == 'sensor_data':
                    # Process sensor data using agent if available
                    if agent:
                        sensor_type = data.get('payload', {}).get('sensor_type', 'unknown')
                        sensor_data = data.get('payload', {}).get('data', {})
                        
                        success = await agent.process_sensor_data(sensor_type, sensor_data)
                        
                        # Acknowledge receipt
                        await websocket.send(json.dumps({
                            "type": "sensor_data_received",
                            "payload": {
                                "sensor_type": sensor_type,
                                "success": success,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    else:
                        # If agent is not available
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Agent is not available to process sensor data",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                # Handle memory search request
                elif msg_type == 'memory_search':
                    # Search memory using agent if available
                    if agent:
                        query = data.get('payload', {}).get('query', '')
                        limit = data.get('payload', {}).get('limit', 5)
                        
                        results = await agent.search_memory(query, limit)
                        
                        # Send back search results
                        await websocket.send(json.dumps({
                            "type": "memory_search_results",
                            "payload": {
                                "query": query,
                                "results": results,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    else:
                        # If agent is not available
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Agent is not available for memory search",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                # Handle LLM requests (different message types that could contain a user query)
                elif msg_type in ['llm_request', 'chat_message', 'user_message']:
                    # Extract the query from the message
                    user_message = extract_message(data)
                    
                    if user_message:
                        logger.info(f"Processing user message: {user_message[:100]}...")
                        
                        # Process message using agent if available
                        if agent:
                            # Let the agent handle the entire process
                            response_data = await agent.process_message(user_message, client_id)
                        else:
                            # Direct LLM call if agent is not available
                            logger.warning("Agent not available, calling LLM directly")
                            if ollama_service:
                                response_data = await ollama_service.generate_response(f"User: {user_message}\nAssistant:")
                            else:
                                response_data = {
                                    "response": "Sorry, both the agent and LLM service are unavailable.",
                                    "error": True,
                                    "timestamp": datetime.now().isoformat()
                                }
                        
                        # Send response back in a format compatible with both old and new clients
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "content": response_data.get("response", "No response generated"),
                            "payload": response_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        logger.info(f"Sent response: {response_data.get('response', '')[:100]}...")
                    else:
                        logger.warning("Received empty message")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "content": "Empty message received",
                            "message": "Empty message received",
                            "timestamp": datetime.now().isoformat()
                        }))
                
                # Handle ping messages
                elif msg_type == 'ping':
                    # Respond with pong
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Also send a status update to keep the connection active
                    status_msg = "Agent-based server is online and ready."
                    
                    await websocket.send(json.dumps({
                        "type": "status_update",
                        "content": status_msg,
                        "payload": {
                            "server_status": "online",
                            "agent_active": agent is not None,
                            "memory_active": agent.memory_system is not None if agent else False,
                            "llm_status": "ready" if ollama_service else "unavailable",
                            "model": ollama_service.model_name if ollama_service else "unknown",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Default response for unknown message types
                else:
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Received unknown message type: {msg_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if client_id in client_info:
            del client_info[client_id]
        logger.info(f"Client {client_id} disconnected")

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
                # Get agent and memory stats if available
                agent_stats = {
                    "active": agent is not None,
                    "memory_active": agent.memory_system is not None if agent else False,
                    "conversation_length": len(agent.conversation_history) if agent else 0
                }
                
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients),
                    "agent": agent_stats
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    global agent, ollama_service
    
    # Initialize ollama service
    logger.info("Initializing Ollama service...")
    ollama_service = OllamaService()
    ollama_initialized = await ollama_service.list_models()
    if not ollama_initialized:
        logger.warning("Failed to initialize Ollama service, will continue without LLM capabilities")
        ollama_service = None
    
    # Initialize memory system
    logger.info("Initializing Memory system...")
    memory_system = await initialize_memory_system()
    if not memory_system:
        logger.warning("Memory system initialization failed, agent will have limited capabilities")
    
    # Initialize agent
    logger.info("Initializing Agent...")
    agent = Agent(memory_system=memory_system, llm_service=ollama_service)
    logger.info("Agent initialized successfully")
    
    # Set up WebSocket server
    port = 8765
    host = "0.0.0.0"  # Listen on all interfaces
    
    # Create directories
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Start the WebSocket server
        async with websockets.serve(
            websocket_handler,
            host,
            port,
            ping_interval=30,
            ping_timeout=10
        ):
            # Save PID
            with open('pids/agent_based_llm_ws.pid', 'w') as f:
                f.write(str(os.getpid()))
                
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            logger.info(f"Using LLM model: {ollama_service.model_name if ollama_service else 'None'}")
            logger.info(f"Agent: {'ACTIVE' if agent else 'INACTIVE'}")
            logger.info(f"Memory system: {'ACTIVE' if memory_system else 'INACTIVE'}")
            
            # Keep running forever
            await asyncio.Future()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        # Clean up memory system
        if memory_system:
            try:
                await memory_system.cleanup()
                logger.info("Memory system cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up memory system: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)