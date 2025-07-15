#!/usr/bin/env python
"""
Working WebSocket Server for RPA + Aiayer Backend

Simple, reliable WebSocket server that bridges the NextGen overlay with the automation system.
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import requests
import time
from datetime import datetime
from typing import Dict, Set, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
connected_clients = set()
rpa_server_url = "http://localhost:16901"
chat_server_url = "http://localhost:5002"
proactive_dashboard_url = "http://localhost:5003"

async def check_backend_services() -> Dict[str, bool]:
    """Check if all backend services are running."""
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
        
    # Check Proactive Dashboard
    try:
        response = requests.get(f"{proactive_dashboard_url}/", timeout=2)
        services['proactive_dashboard'] = response.status_code == 200
    except:
        services['proactive_dashboard'] = False
        
    return services

async def send_to_chat_server(message: str) -> Dict[str, Any]:
    """Send message to chat server and get response."""
    try:
        response = requests.post(
            f"{chat_server_url}/chat",
            json={"message": message},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Chat server returned {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to communicate with chat server: {e}"}

async def execute_rpa_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute RPA action via the Go server."""
    try:
        # Map common actions to RPA endpoints
        if action == "mouse_click":
            x, y = params.get('x', 100), params.get('y', 100)
            response = requests.get(f"{rpa_server_url}/mouse/click/{x}/{y}")
        elif action == "keyboard_type":
            text = params.get('text', '')
            response = requests.get(f"{rpa_server_url}/keyboard/input?text={text}")
        elif action == "screenshot":
            response = requests.get(f"{rpa_server_url}/display/img/0/0/800/600")
        elif action == "launch_app":
            app_name = params.get('app_name', '')
            response = requests.get(f"{rpa_server_url}/system/app/run?app={app_name}")
        else:
            return {"error": f"Unknown action: {action}"}
            
        if response.status_code == 200:
            return {"success": True, "data": response.text}
        else:
            return {"error": f"RPA action failed: {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to execute RPA action: {e}"}

async def handler(websocket, path):
    """Handle WebSocket connections with full backend integration."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        # Check backend services
        services = await check_backend_services()
        
        # Send welcome message with service status
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to Integrated SensAI Backend",
                "services": services,
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                message_type = data.get("type", "")
                payload = data.get("payload", {})
                
                # Handle different message types
                if message_type == "chat_message":
                    # Send to chat server
                    response = await send_to_chat_server(payload.get("message", ""))
                    await websocket.send(json.dumps({
                        "type": "chat_response",
                        "data": response,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif message_type == "rpa_action":
                    # Execute RPA action
                    action = payload.get("action", "")
                    params = payload.get("params", {})
                    response = await execute_rpa_action(action, params)
                    await websocket.send(json.dumps({
                        "type": "rpa_response",
                        "data": response,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()}
                    }))
                    
                elif message_type == "get_status":
                    # Get current system status
                    services = await check_backend_services()
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
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    while True:
        if connected_clients:
            services = await check_backend_services()
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "services": services,
                    "client_count": len(connected_clients),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(5)

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Try different ports if the default one is in use
        ports_to_try = [8767, 8769, 8770, 8771]
        server = None
        
        for port in ports_to_try:
            try:
                server = await websockets.serve(
                    handler,
                    "127.0.0.1",
                    port,
                    ping_interval=10,
                    ping_timeout=5,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                    max_queue=64,               # Queue size
                    close_timeout=2             # Close timeout
                )
                logger.info(f"Working WebSocket server started on ws://127.0.0.1:{port}")
                break
            except OSError as e:
                logger.warning(f"Port {port} is in use, trying another port: {e}")
                continue
                
        if server is None:
            raise OSError("All ports are in use. Cannot start WebSocket server.")
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1) 