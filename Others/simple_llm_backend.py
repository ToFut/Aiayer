#!/usr/bin/env python3
"""
Simple LLM Backend Server
A basic WebSocket server that can handle chat messages and provide simple responses.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/simple_llm_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

class SimpleLLMBackend:
    """Simple LLM backend that provides basic responses to user queries."""
    
    def __init__(self):
        self.responses = [
            "I understand what you're asking. Let me help you with that.",
            "That's an interesting question! Here's what I think...",
            "Based on what you've shared, I can see that you're working on something important.",
            "I'm here to assist you. What would you like to know more about?",
            "That's a great point. Let me provide some insight on that topic.",
            "I can help you with that. Here are some suggestions...",
            "Thanks for that question. Let me think about the best way to approach this.",
            "I see what you're getting at. Here's my perspective on that...",
            "That's definitely worth exploring further. Here's what I'd recommend...",
            "I appreciate you sharing that with me. Let me offer some thoughts..."
        ]
        
    def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate a simple response based on the query."""
        try:
            import random
            
            # Create a context-aware response
            base_response = random.choice(self.responses)
            
            # Add context if available
            if context:
                if 'active_app' in context:
                    base_response += f" I can see you're currently using {context['active_app']}."
                if 'screen_text' in context and context['screen_text']:
                    base_response += " Based on what's on your screen, it looks like you're working on something productive."
            
            # Add query-specific responses
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['hello', 'hi', 'hey']):
                return "Hello! I'm your AI assistant. How can I help you today?"
            
            elif any(word in query_lower for word in ['help', 'assist', 'support']):
                return "I'm here to help! I can assist you with questions, provide information, or help you work through problems. What do you need help with?"
            
            elif any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where']):
                return f"{base_response} Regarding your question about '{query}', let me provide some helpful information."
            
            elif any(word in query_lower for word in ['screen', 'seeing', 'display']):
                return "I can see your screen context and I'm here to help you with whatever you're working on. What would you like to know?"
            
            elif any(word in query_lower for word in ['thanks', 'thank you']):
                return "You're very welcome! I'm glad I could help. Is there anything else you'd like to know?"
            
            else:
                return f"{base_response} Your question '{query}' is interesting, and I'll do my best to provide useful information."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

# Global LLM backend instance
llm_backend = SimpleLLMBackend()

async def handler(websocket: WebSocketServerProtocol):
    """Handle WebSocket connections."""
    client_id = str(uuid.uuid4())
    client_type = "unknown"
    logger.info(f"Client {client_id} connected")
    
    try:
        # Add to connected clients
        connected_clients.add(websocket)
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "payload": {
                "client_id": client_id,
                "message": "Connected to Simple LLM Backend",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                logger.info(f"Received message type {msg_type} from {client_id}")
                
                if msg_type == 'register':
                    # Handle client registration
                    client_type = data.get('client_type', 'unknown')
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        "type": "registration_confirmed",
                        "payload": {
                            "client_id": client_id,
                            "client_type": client_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                elif msg_type == 'user_message':
                    # Handle user messages (the main functionality)
                    payload = data.get('payload', {})
                    query = payload.get('query', '')
                    context = payload.get('context', {})
                    
                    logger.info(f"Processing query: {query[:100]}...")
                    
                    if query:
                        # Generate response using the simple LLM backend
                        response_text = llm_backend.generate_response(query, context)
                        
                        # Send response back
                        await websocket.send(json.dumps({
                            "type": "response",
                            "payload": {
                                "response": response_text,
                                "query": query,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        
                        logger.info(f"Sent response: {response_text[:100]}...")
                    else:
                        # Send error for empty query
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Empty query received",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                elif msg_type == 'ping':
                    # Handle ping
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                else:
                    logger.warning(f"Unhandled message type: {msg_type}")
                    # Echo back with acknowledgment
                    await websocket.send(json.dumps({
                        "type": "ack",
                        "payload": {
                            "message": f"Received {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def main():
    """Main function to start the simple LLM backend server."""
    try:
        port = 8767
        
        # Create the server
        server = await websockets.serve(
            handler,
            "localhost",
            port,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info(f"Simple LLM Backend started on ws://localhost:{port}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/simple_llm_backend.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simple LLM Backend stopped by user")
        # Clean up PID file
        try:
            os.remove('pids/simple_llm_backend.pid')
        except:
            pass
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)