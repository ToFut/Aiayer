#!/usr/bin/env python
"""
Simple Working WebSocket Server

A minimal WebSocket server that works with the current websockets version.
"""
import asyncio
import json
import logging
import websockets
import sys
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
connected_clients = set()
rpa_server_url = "http://localhost:16901"
chat_server_url = "http://localhost:5002"

async def check_services():
    """Check if backend services are running."""
    services = {}
    
    # Check RPA Server
    try:
        response = requests.get(f"{rpa_server_url}/", timeout=2)
        services['rpa_server'] = response.status_code == 200
    except:
        services['rpa_server'] = False
        
    # Check Chat Server
    try:
        response = requests.get(f"{chat_server_url}/", timeout=2)
        services['chat_server'] = response.status_code == 200
    except:
        services['chat_server'] = False
        
    return services

async def handle_websocket(websocket, path=None):
    """Handle WebSocket connections."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Check services
        services = await check_services()
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to SensAI Backend",
                "services": services,
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received: {data}")
                
                message_type = data.get("type", "")
                
                if message_type == "chat_request":
                    # Handle chat requests by sending to chat server
                    user_message = data.get("message", "")
                    mode = data.get("mode", "ask")
                    session_id = data.get("session_id", "")
                    
                    logger.info(f"Processing chat request: {user_message}")
                    
                    try:
                        # Send to chat server
                        response = requests.post(
                            f"{chat_server_url}/chat",
                            json={"message": user_message},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            chat_response = response.json()
                            await websocket.send(json.dumps({
                                "type": "chat_response",
                                "data": {
                                    "message": chat_response.get("response", "Command executed successfully"),
                                    "status": "success",
                                    "mode": mode,
                                    "session_id": session_id
                                },
                                "timestamp": datetime.now().isoformat()
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "chat_response",
                                "data": {
                                    "message": f"Error: Chat server returned {response.status_code}",
                                    "status": "error",
                                    "mode": mode,
                                    "session_id": session_id
                                },
                                "timestamp": datetime.now().isoformat()
                            }))
                    except Exception as e:
                        logger.error(f"Error communicating with chat server: {e}")
                        await websocket.send(json.dumps({
                            "type": "chat_response",
                            "data": {
                                "message": f"Error: {str(e)}",
                                "status": "error",
                                "mode": mode,
                                "session_id": session_id
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()}
                    }))
                
                elif message_type == "get_status":
                    # Get system status
                    services = await check_services()
                    await websocket.send(json.dumps({
                        "type": "status_update",
                        "data": {
                            "services": services,
                            "client_count": len(connected_clients),
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                else:
                    # Echo back unknown messages
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON")
            except Exception as e:
                logger.error(f"Error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        connected_clients.remove(websocket)

async def main():
    """Start the WebSocket server."""
    try:
        # Start server
        async with websockets.serve(handle_websocket, "127.0.0.1", 8767):
            logger.info("WebSocket server started on ws://127.0.0.1:8767")
            await asyncio.Future()  # Run forever
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 