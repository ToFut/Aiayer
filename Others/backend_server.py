import json
import logging
import os
from datetime import datetime
import websockets
import asyncio

# Configure logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/backend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
connected_clients = set()

async def handler(websocket):
    """Handle WebSocket connection"""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Welcome to the backend server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message from client {client_id}: {msg_type}")
                
                if msg_type == 'llm_request':
                    # Handle LLM request
                    query = data.get('payload', {}).get('query', '')
                    logger.info(f"Processing LLM request: {query}")
                    
                    # Send response
                    await websocket.send(json.dumps({
                        "type": "llm_response",
                        "payload": {
                            "response": f"Processed query: {query}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                else:
                    # Echo back with timestamp
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def main():
    """Start the WebSocket server."""
    host = "localhost"
    port = 8767
    
    try:
        server = await websockets.serve(
            handler,
            host,
            port,
            ping_interval=None,
            ping_timeout=None
        )
        
        logger.info(f"Backend server started on ws://{host}:{port}")
        
        # Keep the server running
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 