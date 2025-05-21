import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from websockets.legacy.server import WebSocketServerProtocol
from bridge.message_bridge import MessageBridge, MessageType, MessagePriority, Message
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeServer:
    """WebSocket server that manages frontend and backend connections using MessageBridge"""
    
    def __init__(self, host="localhost", frontend_port=8768, backend_port=8766):
        self.host = host
        self.frontend_port = frontend_port
        self.backend_port = backend_port
        self.frontend_clients = set()
        self.backend_clients = set()
        self.logger = logging.getLogger(__name__)
        self.bridge = MessageBridge()
        self.running = False
        
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle WebSocket connections."""
        try:
            # Determine if this is a frontend or backend connection by port
            local_port = websocket.local_address[1]
            is_frontend = local_port == self.frontend_port
            client_set = self.frontend_clients if is_frontend else self.backend_clients
            
            # Add to appropriate set
            client_set.add(websocket)
            self.logger.info(f"New {'frontend' if is_frontend else 'backend'} client connected")
            
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        self.logger.debug(f"Received message: {data}")
                        
                        # Handle registration messages
                        if data.get('type') == 'register':
                            # Send registration confirmation
                            await websocket.send(json.dumps({
                                'type': 'registration_confirmed',
                                'client_type': data.get('client_type'),
                                'sensor_type': data.get('sensor_type'),
                                'timestamp': datetime.now().timestamp()
                            }))
                            self.logger.info(f"Registration confirmed for {data.get('client_type')} client")
                            continue
                        
                        # Handle sensor data
                        if data.get('type') == 'sensor_data':
                            # Route sensor data to frontend clients
                            if self.frontend_clients:
                                await asyncio.gather(
                                    *[client.send(message) for client in self.frontend_clients],
                                    return_exceptions=True
                                )
                                self.logger.debug(f"Routed sensor data to {len(self.frontend_clients)} frontend clients")
                            continue
                        
                        # Route other messages to appropriate clients
                        target_clients = self.backend_clients if is_frontend else self.frontend_clients
                        if target_clients:
                            await asyncio.gather(
                                *[client.send(message) for client in target_clients],
                                return_exceptions=True
                            )
                    except json.JSONDecodeError:
                        self.logger.error("Invalid JSON received")
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        
            except websockets.exceptions.ConnectionClosed:
                self.logger.info(f"{'Frontend' if is_frontend else 'Backend'} client disconnected")
            finally:
                client_set.remove(websocket)
            
        except Exception as e:
            self.logger.error(f"Error in handler: {e}")
            raise

    async def start(self):
        """Start the bridge server."""
        if self.running:
            return
        
        self.running = True
        
        # Start message bridge
        bridge_task = asyncio.create_task(self.bridge.start())
        
        try:
            # Start frontend server
            frontend_server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.frontend_port
            )
            
            # Start backend server
            backend_server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.backend_port
            )
            
            self.logger.info(f"Bridge server started - Frontend: ws://{self.host}:{self.frontend_port}, Backend: ws://{self.host}:{self.backend_port}")
            
            # Keep the server running
            await asyncio.Future()
            
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            raise

    async def stop(self):
        """Stop the bridge server"""
        if not self.running:
            return
            
        self.running = False
        await self.bridge.stop()
        logger.info("Bridge server stopped")

if __name__ == "__main__":
    # Create and start the bridge server
    server = BridgeServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise 