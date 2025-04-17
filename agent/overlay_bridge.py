import json
import asyncio
import websockets
import threading
import time
from typing import Dict, Any, Callable, List, Set
import logging

logger = logging.getLogger(__name__)

class OverlayBridge:
    """Bridge between Python backend and overlay interface"""
    
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.clients = set()
        self.callback_registry = {}
        self.logger = logger
        
    async def _handler(self, websocket, path):
        """Handle WebSocket connection"""
        self.clients.add(websocket)
        self.logger.info(f"New client connected. Total clients: {len(self.clients)}")
        
        # Send initial status message
        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'payload': {
                    'state': 'connected',
                    'server_time': time.time(),
                    'client_count': len(self.clients)
                }
            }))
        except Exception as e:
            self.logger.error(f"Error sending initial status: {e}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    payload = data.get('payload')
                    
                    self.logger.info(f"Received message of type: {message_type}")
                    
                    # Special handling for connection established message
                    if message_type == 'connection_established':
                        self.logger.info(f"Client identified: {payload.get('client', 'unknown')}, version: {payload.get('version', 'unknown')}")
                        continue
                    
                    # Process registered callbacks
                    if message_type in self.callback_registry:
                        for callback in self.callback_registry[message_type]:
                            await callback(payload)
                    else:
                        self.logger.warning(f"No handler registered for message type: {message_type}")
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"Client connection closed: {e}")
        except Exception as e:
            self.logger.error(f"Error in websocket handler: {e}")
        finally:
            self.clients.remove(websocket)
            self.logger.info(f"Client disconnected. Remaining clients: {len(self.clients)}")
    
    def start(self):
        """Start WebSocket server in background thread"""
        loop = asyncio.new_event_loop()
        
        async def start_server():
            self.server = await websockets.serve(
                self._handler, "localhost", self.port)
            await self.server.wait_closed()
            
        def run_loop():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_server())
            
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        return thread
    
    async def send_message(self, message_type: str, payload: Dict[str, Any]):
        """Send message to all connected clients"""
        try:
            message = json.dumps({
                'type': message_type,
                'payload': payload
            })
            
            if not self.clients:
                return False
                
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
        
    def register_callback(self, message_type: str, callback: Callable):
        """Register callback for specific message type"""
        if message_type not in self.callback_registry:
            self.callback_registry[message_type] = []
        self.callback_registry[message_type].append(callback) 