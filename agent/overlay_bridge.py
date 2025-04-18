import json
import asyncio
import websockets
import threading
import time
from typing import Dict, Any, Callable, List, Set
import logging
from collections import deque

logger = logging.getLogger(__name__)

class OverlayBridge:
    """Bridge between Python backend and overlay interface"""
    
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.clients = set()
        self.callback_registry = {}
        self.logger = logger
        self.loop = None
        self.thread = None
        self.is_running = False
        self.activity_queue = deque(maxlen=20)  # Store recent user activities
        self.queue_lock = threading.Lock()
        
    async def _handler(self, websocket):
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
        self.loop = asyncio.new_event_loop()
        self.is_running = True
        
        async def start_server():
            async with websockets.serve(self._handler, "localhost", self.port):
                self.logger.info(f"WebSocket server running on localhost:{self.port}")
                # Keep the server running until closed
                await asyncio.Future()  # This will run forever until cancelled
            
        def run_loop():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(start_server())
            except asyncio.CancelledError:
                self.logger.info("WebSocket server task cancelled")
            except Exception as e:
                self.logger.error(f"Error in WebSocket server: {e}")
            
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        return self.thread
    
    def stop(self):
        """Stop the WebSocket server"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Close all client connections
        if self.clients:
            for client in list(self.clients):
                close_coro = client.close()
                if self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(close_coro, self.loop)
        
        # Cancel all tasks
        if self.loop and self.loop.is_running():
            for task in asyncio.all_tasks(self.loop):
                task.cancel()
            
            # Create a task to stop the loop
            asyncio.run_coroutine_threadsafe(self._shutdown_loop(), self.loop)
            
        self.logger.info("WebSocket server stopped")
    
    async def _shutdown_loop(self):
        """Shutdown the event loop gracefully"""
        # Sleep briefly to allow other tasks to be cancelled
        await asyncio.sleep(0.1)
        self.loop.stop()
    
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
            
    async def add_system_activity(self, activity_type: str, details: Dict[str, Any]):
        """Add user activity to the queue and notify clients"""
        timestamp = time.time()
        activity = {
            "type": activity_type,
            "details": details,
            "timestamp": timestamp
        }
        
        with self.queue_lock:
            self.activity_queue.append(activity)
        
        # Notify all connected clients about the new activity
        await self.send_message("system_activity", {
            "activity": activity,
            "recent_count": len(self.activity_queue)
        })
        
        return True
        
    async def send_sensor_data(self, sensor_data: Dict[str, Any]):
        """Send sensor data to all connected clients"""
        return await self.send_message("sensor_data", sensor_data)
        
    def register_callback(self, message_type: str, callback: Callable):
        """Register callback for specific message type"""
        if message_type not in self.callback_registry:
            self.callback_registry[message_type] = []
        self.callback_registry[message_type].append(callback) 