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
import time

# Configure logging
os.makedirs('logs', exist_ok=True)
os.makedirs('logs/llm', exist_ok=True)

# Create a custom filter to prevent duplicate logs
class DuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log = None
        self.last_time = None
        self.min_interval = 30  # Minimum seconds between similar logs
        self.connection_logs = set()  # Track unique connections

    def filter(self, record):
        # Skip connection logs for already logged connections
        if "WebSocket connection established" in record.getMessage():
            client_id = record.getMessage().split("from ")[-1]
            if client_id in self.connection_logs:
                return False
            self.connection_logs.add(client_id)
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
            'logs/llm/self_contained_llm.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=2
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('self_contained_llm')
logger.addFilter(DuplicateFilter())

# Reduce logging level for all modules
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('uvicorn').setLevel(logging.ERROR)
logging.getLogger('fastapi').setLevel(logging.ERROR)

# WebSocket clients
connected_clients = set()
client_info = {}  # Store client info by ID

# WebSocket server configuration
WS_HOST = "0.0.0.0"
WS_PORT = 8770  # Changed from 8766 to avoid port conflict

class OllamaService:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:latest"  # Default model, will try to find best available
        
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
async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    try:
        # Simple welcome message
        await websocket.send(json.dumps({"type": "welcome"}))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                if msg_type == 'llm_request':
                    user_message = extract_message(data)
                    if user_message:
                        response_data = await ollama_service.generate_response(user_message)
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "content": response_data.get("response", "No response generated")
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Empty message received"
                        }))
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

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
    """Main function to start the WebSocket server"""
    try:
        # Initialize Ollama service
        if not await ollama_service.list_models():
            logger.error("Failed to initialize Ollama service")
            return
        
        # Start WebSocket server with basic configuration
        server = await websockets.serve(
            websocket_handler, 
            WS_HOST, 
            WS_PORT,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=1,
            max_size=1024*1024,
            compression=None
        )
        
        logger.info(f"WebSocket server started on ws://{WS_HOST}:{WS_PORT}")
        await server.wait_closed()
            
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)