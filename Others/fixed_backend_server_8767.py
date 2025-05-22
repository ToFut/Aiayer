#!/usr/bin/env python3
"""
Fixed Simple WebSocket Server on Port 8767
Backend server with proper LLM integration and error handling.
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import uuid
from datetime import datetime
from typing import Set
from websockets.server import WebSocketServerProtocol

# Configure logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/backend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients: Set[WebSocketServerProtocol] = set()
client_types = {}
registered_clients = set()

async def get_llm_response(query: str) -> str:
    """Get response from LLM service (Ollama)."""
    try:
        import aiohttp
        
        # Try to connect to Ollama
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "llama3.2:1b",
                "prompt": f"You are a helpful AI assistant. Please respond to this query in a concise and helpful way: {query}",
                "stream": False
            }
            
            async with session.post('http://localhost:11434/api/generate', json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', 'I apologize, but I received an empty response.')
                else:
                    logger.error(f"Ollama API returned status {response.status}")
                    return "I'm having trouble connecting to the AI service right now."
                    
    except ImportError:
        logger.warning("aiohttp not available, using simple response")
        return f"I received your message: '{query}'. I'm a simple backend server and would normally connect to an LLM service to provide better responses."
    except Exception as e:
        logger.error(f"Error getting LLM response: {e}")
        return "I'm experiencing technical difficulties right now, but I'm here to help!"

async def handler(websocket: WebSocketServerProtocol, path: str):
    """Handle WebSocket connections."""
    client_id = str(uuid.uuid4())
    client_type = "unknown"
    is_registered = False
    
    try:
        # Add client to set
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "payload": {
                "client_id": client_id,
                "message": f"Connected to backend server at path: {path}",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type {msg_type} from client {client_id}")
                
                # Handle registration
                if msg_type in ['register', 'connection_established']:
                    client_type = data.get('client_type', data.get('payload', {}).get('client_type', 'unknown'))
                    client_types[websocket] = client_type
                    registered_clients.add(websocket)
                    is_registered = True
                    
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        "type": "registration_confirmed",
                        "payload": {
                            "client_id": client_id,
                            "client_type": client_type,
                            "message": "Successfully registered with backend server",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                elif not is_registered:
                    # Require registration first
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": "Please register first before sending other messages",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    continue
                
                # Handle user queries
                elif msg_type == 'user_interaction':
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"Processing query from {client_id}: {query}")
                        
                        # Get LLM response
                        response = await get_llm_response(query)
                        
                        # Send response back
                        await websocket.send(json.dumps({
                            "type": "query_response",
                            "payload": {
                                "response": response,
                                "query": query,
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id
                            }
                        }))
                        
                        logger.info(f"Sent response to {client_id}")
                    else:
                        logger.warning(f"Unknown user_interaction type: {payload.get('type')}")
                
                # Handle context requests
                elif msg_type == 'context_request':
                    await websocket.send(json.dumps({
                        "type": "context_response",
                        "payload": {
                            "context": {
                                "server": "backend_server_8767",
                                "clients_connected": len(connected_clients),
                                "registered_clients": len(registered_clients),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    }))
                
                # Handle heartbeat
                elif msg_type == 'heartbeat':
                    await websocket.send(json.dumps({
                        "type": "heartbeat_ack",
                        "payload": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": f"Unknown message type: {msg_type}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": f"Server error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        # Clean up
        connected_clients.discard(websocket)
        if websocket in client_types:
            del client_types[websocket]
        if websocket in registered_clients:
            registered_clients.discard(websocket)
        logger.info(f"Client {client_id} ({client_type}) cleaned up")

async def main():
    """Start the backend server."""
    try:
        port = 8767
        
        # Check if port is in use
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                logger.error(f"Port {port} is already in use")
                # Kill existing process
                os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
                await asyncio.sleep(2)
        
        # Create PID file
        os.makedirs("pids", exist_ok=True)
        with open('pids/backend_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start server
        logger.info(f"Starting backend server on port {port}")
        async with websockets.serve(handler, "localhost", port):
            logger.info(f"Backend server listening on ws://localhost:{port}")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
    finally:
        # Clean up PID file
        try:
            os.remove('pids/backend_server.pid')
        except:
            pass
        logger.info("Backend server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)