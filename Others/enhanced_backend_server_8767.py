#!/usr/bin/env python3
"""
Enhanced Backend Server on Port 8767
Handles LLM queries with memory integration and meaningful responses
"""
import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime
import requests
from pathlib import Path

# Configure logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_backend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
client_types = {}

class MemoryManager:
    """Manages memory and context for LLM queries"""
    
    def __init__(self):
        self.memory_path = Path("memory")
        self.memory_path.mkdir(exist_ok=True)
    
    def load_context(self):
        """Load current context from memory"""
        try:
            context_file = self.memory_path / "last_context.json"
            if context_file.exists():
                with open(context_file, 'r') as f:
                    context = json.load(f)
                    return context
            return {}
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return {}
    
    def load_memory_state(self):
        """Load memory state"""
        try:
            memory_file = self.memory_path / "memory_state.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory = json.load(f)
                    return memory
            return {}
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            return {}
    
    def save_conversation(self, query, response):
        """Save conversation to memory"""
        try:
            conversation_file = self.memory_path / "conversation_history.json"
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response
            }
            
            conversations = []
            if conversation_file.exists():
                try:
                    with open(conversation_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            conversations = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Invalid conversation history file, starting fresh")
                    conversations = []
            
            conversations.append(conversation_entry)
            
            # Keep only last 50 conversations
            conversations = conversations[-50:]
            
            with open(conversation_file, 'w') as f:
                json.dump(conversations, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

class LLMProcessor:
    """Processes LLM queries with context awareness"""
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:latest"  # Default model
        
    async def process_query(self, query_text, context=None):
        """Process LLM query with context"""
        try:
            # Load context and memory
            current_context = self.memory_manager.load_context()
            memory_state = self.memory_manager.load_memory_state()
            
            # Build context-aware prompt
            prompt = self.build_context_prompt(query_text, current_context, memory_state, context)
            
            # Try Ollama first
            response = await self.query_ollama(prompt)
            
            if not response or response == "thinking...":
                # Fallback to local processing
                response = await self.local_processing(query_text, current_context)
            
            # Save conversation
            self.memory_manager.save_conversation(query_text, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def build_context_prompt(self, query, context, memory, additional_context=None):
        """Build context-aware prompt"""
        prompt_parts = []
        
        # Add system context
        prompt_parts.append("You are an AI assistant with access to the user's screen and system context.")
        
        # Add current context
        if context and context.get('active_app'):
            prompt_parts.append(f"Current application: {context.get('active_app')}")
        
        if context and context.get('active_window'):
            prompt_parts.append(f"Current window: {context.get('active_window')}")
        
        if context and context.get('screen_text'):
            screen_text = context.get('screen_text', '')[:500]  # Limit context size
            if screen_text:
                prompt_parts.append(f"Current screen content: {screen_text}")
        
        # Add memory context
        if memory and memory.get('short_term'):
            recent_items = memory.get('short_term', [])[-3:]  # Last 3 items
            if recent_items:
                prompt_parts.append(f"Recent activity: {json.dumps(recent_items)}")
        
        # Add additional context
        if additional_context:
            prompt_parts.append(f"Additional context: {additional_context}")
        
        # Add the user query
        prompt_parts.append(f"User query: {query}")
        prompt_parts.append("Please provide a helpful and relevant response based on the context provided.")
        
        return "\n\n".join(prompt_parts)
    
    async def query_ollama(self, prompt):
        """Query Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 512
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama service not available")
            return None
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return None
    
    async def local_processing(self, query, context):
        """Local processing fallback"""
        query_lower = query.lower()
        
        # Context-aware responses
        if context and context.get('active_app'):
            app = context.get('active_app', '').lower()
            
            if 'chrome' in app or 'safari' in app or 'firefox' in app:
                if 'what' in query_lower or 'help' in query_lower:
                    return f"I can see you're using {context.get('active_app')}. I can help you with web browsing, searching, or explaining content on the current page."
            
            elif 'code' in app or 'vscode' in app or 'sublime' in app:
                if 'what' in query_lower or 'help' in query_lower:
                    return f"I can see you're coding in {context.get('active_app')}. I can help with code review, debugging, explaining concepts, or suggesting improvements."
            
            elif 'terminal' in app or 'iterm' in app:
                if 'what' in query_lower or 'help' in query_lower:
                    return f"I can see you're using the terminal. I can help with command explanations, troubleshooting, or suggesting terminal commands."
        
        # General responses based on query content
        if 'hello' in query_lower or 'hi' in query_lower:
            return f"Hello! I can see your current context and I'm ready to help. What would you like to know?"
        
        elif 'what' in query_lower and ('doing' in query_lower or 'working' in query_lower):
            if context and context.get('active_app'):
                return f"I can see you're currently using {context.get('active_app')}. How can I assist you with what you're working on?"
            else:
                return "I can see your screen context. What specifically would you like help with?"
        
        elif 'help' in query_lower:
            return "I'm your AI assistant with access to your screen context. I can help explain what you're seeing, answer questions about your current work, or provide assistance with various tasks. What do you need help with?"
        
        elif 'test' in query_lower:
            return f"Test response received! I can see your context and I'm processing queries successfully. Current time: {datetime.now().strftime('%H:%M:%S')}"
        
        else:
            # Generic contextual response
            context_info = ""
            if context and context.get('active_app'):
                context_info = f" I can see you're using {context.get('active_app')}."
            
            return f"I understand you're asking: '{query}'. {context_info} Could you provide more details about what specifically you'd like help with?"

memory_manager = MemoryManager()
llm_processor = LLMProcessor(memory_manager)

async def handle_client_message(websocket, message_data, client_id):
    """Handle messages from clients"""
    try:
        msg_type = message_data.get('type', 'unknown')
        
        if msg_type == 'register':
            # Handle client registration
            client_type = message_data.get('client_type', 'unknown')
            client_types[websocket] = client_type
            
            await websocket.send(json.dumps({
                "type": "registration_confirmed",
                "client_id": client_id,
                "client_type": client_type,
                "timestamp": datetime.now().isoformat()
            }))
            
            logger.info(f"Client {client_id} registered as {client_type}")
            
        elif msg_type == 'query':
            # Handle LLM query
            query_text = message_data.get('message', message_data.get('query', ''))
            context = message_data.get('context', message_data.get('payload', {}))
            
            logger.info(f"Processing query from {client_id}: {query_text}")
            
            # Send thinking message
            await websocket.send(json.dumps({
                "type": "response",
                "response": "thinking...",
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Process the query
            response = await llm_processor.process_query(query_text, context)
            
            # Send response
            await websocket.send(json.dumps({
                "type": "response",
                "response": response,
                "status": "completed",
                "query": query_text,
                "timestamp": datetime.now().isoformat()
            }))
            
            logger.info(f"Sent response to {client_id}: {response[:100]}...")
            
        elif msg_type == 'ping':
            # Handle ping
            await websocket.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
            
        else:
            # Unknown message type - echo back
            await websocket.send(json.dumps({
                "type": "echo",
                "original_message": message_data,
                "timestamp": datetime.now().isoformat()
            }))
            
    except Exception as e:
        logger.error(f"Error handling message from {client_id}: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))

async def handler(websocket):
    """Handle WebSocket connections with proper signature"""
    client_id = f"client_{len(connected_clients) + 1}_{datetime.now().strftime('%H%M%S')}"
    path = websocket.path if hasattr(websocket, 'path') else '/'
    
    try:
        # Add client to set
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "message": f"Connected to Enhanced Backend Server",
            "capabilities": ["llm_queries", "context_awareness", "memory_integration"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_client_message(websocket, data, client_id)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.discard(websocket)
        client_types.pop(websocket, None)

async def broadcast_status():
    """Periodically broadcast status updates to all clients"""
    while True:
        if connected_clients:
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "timestamp": datetime.now().isoformat(),
                    "memory_available": os.path.exists("memory/memory_state.json"),
                    "context_available": os.path.exists("memory/last_context.json")
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(30)  # Every 30 seconds

async def main():
    """Main function to start the Enhanced Backend Server"""
    try:
        logger.info("Starting Enhanced Backend Server...")
        
        # Start the WebSocket server
        server = await websockets.serve(
            handler,
            "127.0.0.1",
            8767,
            ping_interval=20,
            ping_timeout=10,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64,               # Queue size
            close_timeout=5             # Close timeout
        )
        
        logger.info(f"Enhanced Backend Server started on ws://127.0.0.1:8767")
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting Enhanced Backend Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Enhanced Backend Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)