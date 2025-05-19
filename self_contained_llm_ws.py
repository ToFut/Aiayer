#!/usr/bin/env python3
"""
Self-contained WebSocket server with LocalLLM integration
This single script provides a complete solution for chat overlay with LLM functionality
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import aiohttp
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/self_contained_llm_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('self_contained_llm')

# WebSocket clients
connected_clients = set()
client_info = {}  # Store client info by ID

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
        
    async def generate_response(self, query):
        """Generate a response using Ollama API"""
        try:
            logger.info(f"Generating response for query: {query[:100]}...")
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": query,
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
            
# Initialize LLM service
ollama_service = OllamaService()

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

# WebSocket handler
async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    client_info[client_id] = {"type": "unknown", "connected_at": datetime.now().isoformat(), "path": path}
    logger.info(f"Client {client_id} connected on path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Self-contained LLM WebSocket Server",
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
                            "model": ollama_service.model_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Handle status or context request
                elif msg_type == 'status_request' or msg_type == 'context_request':
                    # Send status response
                    await websocket.send(json.dumps({
                        "type": "status_response",
                        "payload": {
                            "connected_clients": len(connected_clients),
                            "model": ollama_service.model_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Also send a context update that the overlay expects
                    await websocket.send(json.dumps({
                        "type": "context_update",
                        "payload": {
                            "context": {
                                "active_window": "Self-contained LLM Chat",
                                "active_app": "Chat Overlay"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Send a welcome message for better visibility
                    welcome_message = "Hello! I'm your local LLM assistant (using " + ollama_service.model_name + "). You can send me messages and I'll respond using your local Ollama installation. What would you like to talk about?"
                    await websocket.send(json.dumps({
                        "type": "llm_response",
                        "content": welcome_message,
                        "payload": {
                            "response": welcome_message,
                            "model": ollama_service.model_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Handle LLM requests (different message types that could contain a user query)
                elif msg_type in ['llm_request', 'chat_message', 'user_message']:
                    # Extract the query from the message
                    user_message = extract_message(data)
                    
                    if user_message:
                        logger.info(f"Processing user message: {user_message[:100]}...")
                        
                        # Generate LLM response
                        response_data = await ollama_service.generate_response(user_message)
                        
                        # Send response back in a format compatible with both old and new clients
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "content": response_data.get("response", "No response generated"),
                            "payload": response_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        logger.info(f"Sent LLM response: {response_data.get('response', '')[:100]}...")
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
                    status_msg = f"Server is online and ready. Using model: {ollama_service.model_name}"
                    await websocket.send(json.dumps({
                        "type": "status_update",
                        "content": status_msg,
                        "payload": {
                            "server_status": "online",
                            "llm_status": "ready",
                            "model": ollama_service.model_name,
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
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients)
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    # Initialize ollama service
    logger.info("Initializing Ollama service...")
    await ollama_service.list_models()
    
    # Set up WebSocket server
    port = 8765
    host = "0.0.0.0"  # Listen on all interfaces
    
    # Create directories
    os.makedirs("pids", exist_ok=True)
    
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Start the WebSocket server
        async with websockets.serve(websocket_handler, host, port):
            # Save PID
            with open('pids/self_contained_llm_ws.pid', 'w') as f:
                f.write(str(os.getpid()))
                
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            logger.info(f"Using LLM model: {ollama_service.model_name}")
            
            # Keep running forever
            await asyncio.Future()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)