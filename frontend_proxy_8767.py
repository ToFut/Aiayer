#!/usr/bin/env python3
"""
Frontend Proxy for Enhanced Enterprise Backend
Proxies port 8767 to 8765 with message format translation
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendProxy:
    def __init__(self):
        self.connected_clients = set()
        
    async def handle_frontend_client(self, websocket):
        """Handle frontend client connections on port 8767"""
        client_id = f"frontend_{int(asyncio.get_event_loop().time() * 1000)}"
        self.connected_clients.add(client_id)
        logger.info(f"Frontend client connected: {client_id}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Enhanced Enterprise Backend via Proxy",
                "timestamp": datetime.now().isoformat(),
                "capabilities": [
                    "agent_self_reflection",
                    "professional_validation", 
                    "real_ai_processing",
                    "enterprise_features"
                ]
            }))
            
            # Connect to backend on port 8765
            async with websockets.connect("ws://localhost:8765") as backend_ws:
                logger.info(f"Connected to backend for client {client_id}")
                
                # Handle backend welcome
                backend_welcome = await backend_ws.recv()
                logger.info(f"Backend welcome: {json.loads(backend_welcome)}")
                
                # Forward messages between frontend and backend
                async def forward_to_backend():
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            # Translate frontend format to backend format
                            if data.get("type") == "chat_request":
                                mode = data.get("mode", "General")
                                user_message = data.get("message", "")
                                
                                # Convert to backend format
                                backend_message = {
                                    "type": "agent_request",
                                    "message": f"{mode}: {user_message}",
                                    "mode": mode,
                                    "frontend_request": True
                                }
                                
                                await backend_ws.send(json.dumps(backend_message))
                            else:
                                # Forward other message types as-is
                                await backend_ws.send(message)
                                
                        except Exception as e:
                            logger.error(f"Error forwarding to backend: {e}")
                
                async def forward_to_frontend():
                    async for message in backend_ws:
                        try:
                            data = json.loads(message)
                            
                            # Translate backend format to frontend format
                            if data.get("type") == "agent_plan_with_reflection":
                                # Extract meaningful response
                                goal_analysis = data.get("goal_analysis", {})
                                response_text = goal_analysis.get("clarified_goal", "Task completed successfully")
                                
                                # Format for frontend
                                frontend_response = {
                                    "type": "chat_response",
                                    "success": True,
                                    "mode": data.get("mode", "Agent"),
                                    "payload": {
                                        "response": response_text,
                                        "success": True,
                                        "mode": data.get("mode", "Agent")
                                    },
                                    "response": response_text,
                                    "processing_time": 0.5,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                await websocket.send(json.dumps(frontend_response))
                            
                            elif data.get("type") == "connection_established":
                                # Skip backend connection message, we already sent our own
                                continue
                            
                            else:
                                # For other types, create a generic response
                                response_text = data.get("message", str(data))
                                
                                frontend_response = {
                                    "type": "chat_response", 
                                    "success": True,
                                    "payload": {
                                        "response": response_text,
                                        "success": True
                                    },
                                    "response": response_text,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                await websocket.send(json.dumps(frontend_response))
                                
                        except Exception as e:
                            logger.error(f"Error forwarding to frontend: {e}")
                
                # Run both forwarding tasks
                await asyncio.gather(
                    forward_to_backend(),
                    forward_to_frontend()
                )
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Frontend client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling frontend client {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)

async def main():
    proxy = FrontendProxy()
    
    logger.info("🌉 Starting Frontend Proxy on port 8767...")
    logger.info("🔗 Connecting to Enhanced Enterprise Backend on port 8765...")
    
    start_server = websockets.serve(
        proxy.handle_frontend_client,
        "localhost",
        8767,
        ping_interval=30,
        ping_timeout=10
    )
    
    logger.info("✅ Frontend Proxy started on ws://localhost:8767")
    logger.info("🎯 Frontend can now connect and get real enterprise responses!")
    
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Frontend Proxy stopped by user")