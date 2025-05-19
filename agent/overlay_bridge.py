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
    
    def __init__(self, port=8766):  # Updated to use the interceptor service port
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
        self.last_heartbeat = {}  # Track last heartbeat per client
        self.current_context = {}  # Store current context
        
        # Register default handlers
        self.register_callback('heartbeat', self._handle_heartbeat)
        self.register_callback('user_interaction', self._handle_user_interaction)
        self.register_callback('context_update', self._handle_context_update)
        
    async def _handler(self, websocket, path):
        """Handle WebSocket connection with correct path parameter"""
        client_id = id(websocket)
        self.clients.add(websocket)
        self.last_heartbeat[client_id] = time.time()
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
                    
                    # Update last heartbeat on any message
                    self.last_heartbeat[client_id] = time.time()
                    
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
            if client_id in self.last_heartbeat:
                del self.last_heartbeat[client_id]
            self.logger.info(f"Client disconnected. Remaining clients: {len(self.clients)}")
    
    async def _check_heartbeats(self):
        """Check client heartbeats and disconnect stale clients"""
        current_time = time.time()
        stale_clients = []
        
        for client in self.clients:
            client_id = id(client)
            if client_id in self.last_heartbeat:
                if current_time - self.last_heartbeat[client_id] > 30:  # 30 seconds timeout
                    stale_clients.append(client)
        
        for client in stale_clients:
            self.logger.warning(f"Client {id(client)} heartbeat timeout, disconnecting...")
            await client.close()
            self.clients.remove(client)
            del self.last_heartbeat[id(client)]
    
    def start(self):
        """Start WebSocket server in background thread"""
        self.loop = asyncio.new_event_loop()
        self.is_running = True
        
        async def start_server():
            async with websockets.serve(self._handler, "localhost", self.port):
                self.logger.info(f"WebSocket server running on localhost:{self.port}")
                
                # Start heartbeat checker
                heartbeat_task = asyncio.create_task(self._check_heartbeats())
                
                # Keep the server running until closed
                await asyncio.Future()  # This will run forever until cancelled
                
                # Cleanup
                heartbeat_task.cancel()
            
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
        
    async def _handle_context_update(self, payload):
        """Handle context update messages"""
        self.current_context = payload
        self.logger.info(f"Context updated: {payload.get('summary', 'No summary')}")
        
        # If there are suggestions, send them as a separate message
        if 'suggestions' in payload and payload['suggestions']:
            await self.send_message('suggestions', {
                'suggestions': payload['suggestions'],
                'context': payload.get('summary', '')
            })
    
    async def _handle_heartbeat(self, payload):
        """Handle heartbeat messages"""
        # Heartbeat is already handled in _handler by updating last_heartbeat
        pass
        
    async def _handle_user_interaction(self, payload):
        """Handle user interaction messages"""
        self.logger.info(f"Received user interaction: {payload}")
        
        # Add context to interaction
        interaction_with_context = {
            **payload,
            'context': self.current_context,
            'timestamp': time.time()
        }
        
        # Add to activity queue
        await self.add_system_activity("user_interaction", interaction_with_context)
        
        # If this is a query, include relevant context in the response
        if payload.get('type') == 'query':
            query = payload.get('query', '')
            context_summary = self.current_context.get('summary', '')
            
            # Send response with context
            await self.send_message('query_response', {
                'query': query,
                'context': context_summary,
                'suggestions': self.current_context.get('suggestions', []),
                'timestamp': time.time()
            }) 
    
    async def send_proactive_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Send proactive suggestions to all connected clients
        
        Args:
            suggestions: List of suggestion objects to display in the UI
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not suggestions:
            self.logger.debug("No suggestions to send")
            return False
            
        self.logger.info(f"Sending {len(suggestions)} proactive suggestions to clients")
        
        # Format suggestions for the UI
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestion = {
                'id': suggestion.get('suggestion_id'),
                'title': suggestion.get('title'),
                'content': suggestion.get('content'),
                'action': suggestion.get('action_data'),
                'urgency': suggestion.get('urgency', 3),
                'category': suggestion.get('category', 'general'),
                'buttons': [
                    {'id': 'do', 'label': 'Do', 'primary': True},
                    {'id': 'adjust', 'label': 'Adjust', 'primary': False},
                    {'id': 'dismiss', 'label': 'No', 'primary': False}
                ]
            }
            formatted_suggestions.append(formatted_suggestion)
            
        # Add high-priority suggestions as system activity for visibility
        high_priority_suggestions = [s for s in suggestions if s.get('urgency', 0) >= 4]
        if high_priority_suggestions:
            for suggestion in high_priority_suggestions:
                await self.add_system_activity("suggestion", {
                    'suggestion_id': suggestion.get('suggestion_id'),
                    'title': suggestion.get('title'),
                    'urgency': suggestion.get('urgency', 3)
                })
        
        # Send suggestions
        return await self.send_message('suggestions', formatted_suggestions)
        
    def register_suggestion_feedback_handler(self, callback: Callable):
        """
        Register a callback to handle suggestion feedback
        
        Args:
            callback: Function to call when feedback is received
        """
        self.register_callback('suggestion_feedback', callback)
        self.logger.info("Registered suggestion feedback handler")