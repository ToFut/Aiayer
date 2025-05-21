import json
import asyncio
import websockets
import threading
import time
from typing import Dict, Any, Callable, List, Set
import logging
import traceback
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

class OverlayBridge:
    """Bridge between Python backend and overlay interface"""
    
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
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
        self.message_queue = asyncio.Queue()
        self.batch_size = 5  # Process messages in batches
        self.batch_timeout = 0.1  # 100ms timeout for batching
        self.running = True
        
        # Register default handlers
        self.register_callback('heartbeat', self._handle_heartbeat)
        self.register_callback('user_interaction', self._handle_user_interaction)
        self.register_callback('context_update', self._handle_context_update)
        
    async def start(self):
        """Start the WebSocket server with optimized settings"""
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,  # Reduced from default
            ping_timeout=10,   # Reduced from default
            max_size=1024*1024,  # 1MB max message size
            compression=None  # Disable compression for lower latency
        )
        
        # Start message processing task
        asyncio.create_task(self._process_message_queue())
        
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()
        
    async def _process_message_queue(self):
        """Process messages in batches for better performance"""
        while self.running:
            try:
                # Collect messages for batch processing
                messages = []
                try:
                    # Get first message
                    messages.append(await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=self.batch_timeout
                    ))
                    
                    # Try to get more messages without blocking
                    while len(messages) < self.batch_size:
                        try:
                            messages.append(self.message_queue.get_nowait())
                        except asyncio.QueueEmpty:
                            break
                            
                except asyncio.TimeoutError:
                    if not messages:
                        continue
                
                # Process batch
                if messages:
                    await self._broadcast_batch(messages)
                    
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
                
    async def _broadcast_batch(self, messages):
        """Broadcast a batch of messages to all clients"""
        if not self.clients:
            return
            
        # Prepare batch message
        batch = {
            "type": "batch",
            "messages": messages,
            "timestamp": datetime.now().isoformat()
        }
        
        # Convert to JSON once
        batch_json = json.dumps(batch)
        
        # Broadcast to all clients
        websockets_to_remove = set()
        for websocket in self.clients:
            try:
                await websocket.send(batch_json)
            except websockets.exceptions.ConnectionClosed:
                websockets_to_remove.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                websockets_to_remove.add(websocket)
                
        # Remove disconnected clients
        self.clients -= websockets_to_remove
    
    async def _handler(self, websocket, path):
        """Handle WebSocket connection with correct path parameter"""
        client_id = id(websocket)
        self.clients.add(websocket)
        self.last_heartbeat[client_id] = time.time()
        self.logger.info(f"New client connected. Total clients: {len(self.clients)}")
        
        # Send initial registration message
        try:
            await websocket.send(json.dumps({
                'type': 'register',
                'client_type': 'ui',
                'version': '1.0.0',
                'capabilities': ['overlay_display', 'user_interaction', 'context_tracking']
            }))
            self.logger.info("Sent registration message to bridge server")
            
            # Wait for registration confirmation
            registered = False
            registration_timeout = 10  # seconds
            registration_start = time.time()
            
            while not registered and time.time() - registration_start < registration_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'registration_confirmed':
                        self.logger.info("Registration confirmed by bridge server")
                        registered = True
                        break
                    elif data.get('type') == 'error':
                        self.logger.error(f"Registration error: {data.get('message', 'Unknown error')}")
                        # Store message for processing
                        await self._process_message(websocket, data)
                    else:
                        # Other messages should be processed normally
                        await self._process_message(websocket, data)
                except asyncio.TimeoutError:
                    self.logger.warning("Waiting for registration confirmation...")
                except Exception as e:
                    self.logger.error(f"Error during registration confirmation: {e}")
                    await asyncio.sleep(1)
            
            if not registered:
                self.logger.error("Failed to confirm registration with bridge server")
                await websocket.close(1000, "Registration failed")
                return
                
        except Exception as e:
            self.logger.error(f"Error sending registration: {e}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    self.logger.info(f"Received message of type: {message_type}")
                    
                    # Process the message using the common method
                    await self._process_message(websocket, data)
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"Client connection closed: {e}")
        except Exception as e:
            self.logger.error(f"Error in websocket handler: {e}")
            self.logger.error(traceback.format_exc())
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
        
    async def _process_message(self, websocket, data):
        """Process a WebSocket message"""
        try:
            message_type = data.get('type')
            payload = data.get('payload', {})
            
            # Update last heartbeat on any message
            client_id = id(websocket)
            self.last_heartbeat[client_id] = time.time()
            
            # Process registered callbacks
            if message_type in self.callback_registry:
                for callback in self.callback_registry[message_type]:
                    await callback(payload)
            else:
                self.logger.debug(f"No handler registered for message type: {message_type}")
                
            # Handle LLM requests with context
            if message_type in ['llm_request', 'chat_message', 'user_message']:
                # Get current context
                context = self.current_context.copy()
                
                # Add screen sensor data if available
                if hasattr(self, 'screen_data') and self.screen_data:
                    context['screen'] = self.screen_data
                
                # Add process data if available
                if hasattr(self, 'process_data') and self.process_data:
                    context['processes'] = self.process_data
                
                # Add context to the message
                enriched_data = {
                    'type': message_type,
                    'payload': {
                        **payload,
                        'context': context
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Forward to LLM service
                await self.send_message('llm_request', enriched_data['payload'])
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.logger.error(traceback.format_exc())
    
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
        """Handle context update messages with semantic search support"""
        self.current_context = payload
        
        # Check if this is a semantic search-based context
        if 'search_method' in payload and payload['search_method'] == 'semantic_search':
            relevant_count = len(payload.get('relevant_messages', []))
            self.logger.info(f"Context updated with semantic search: {relevant_count} relevant messages")
            
            # Create a summary from the relevant messages
            if not payload.get('summary') and relevant_count > 0:
                # Generate a simple summary based on relevant messages
                payload['summary'] = f"Context includes {relevant_count} semantically relevant messages"
        else:
            self.logger.info(f"Context updated: {payload.get('summary', 'No summary')}")
        
        # If there are suggestions, send them as a separate message
        if 'suggestions' in payload and payload['suggestions']:
            context_data = {
                'suggestions': payload['suggestions'],
                'context': payload.get('summary', ''),
                'search_method': payload.get('search_method', 'standard')
            }
            
            # Add relevant messages if available
            if 'relevant_messages' in payload:
                context_data['relevant_messages'] = payload['relevant_messages']
                
            await self.send_message('suggestions', context_data)
    
    async def _handle_heartbeat(self, payload):
        """Handle heartbeat messages"""
        # Heartbeat is already handled in _handler by updating last_heartbeat
        pass
        
    async def _handle_user_interaction(self, payload):
        """Handle user interaction messages with semantic search-based context"""
        self.logger.info(f"Received user interaction: {payload}")
        
        # Add context to interaction
        interaction_with_context = {
            **payload,
            'context': self.current_context,
            'timestamp': time.time()
        }
        
        # Add to activity queue
        await self.add_system_activity("user_interaction", interaction_with_context)
        
        # If this is a query, include semantically relevant context in the response
        if payload.get('type') == 'query':
            query = payload.get('query', '')
            
            # Use semantic search context if available, otherwise fall back to summary
            if 'relevant_messages' in self.current_context:
                context_data = {
                    'relevant_messages': self.current_context.get('relevant_messages', []),
                    'search_method': self.current_context.get('search_method', 'semantic_search'),
                    'summary': self.current_context.get('summary', '')
                }
            else:
                context_data = {
                    'summary': self.current_context.get('summary', ''),
                    'search_method': 'legacy'
                }
            
            self.logger.info(f"Including semantic search context in query response (method: {context_data.get('search_method', 'unknown')})")
            
            # Send response with semantically relevant context
            await self.send_message('query_response', {
                'query': query,
                'context': context_data,
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
        
        # Send individual suggestion messages to ensure proper handling in UI
        for suggestion in formatted_suggestions:
            # Send as a single suggestion for better UI compatibility
            await self.send_message('suggestion', {
                'content': suggestion['content'],
                'title': suggestion['title'],
                'isSuggestion': True, # Explicitly mark as suggestion for UI
                'buttons': suggestion['buttons']
            })
            
        # Also send the batch for backwards compatibility
        return await self.send_message('suggestions', formatted_suggestions)
        
    def register_suggestion_feedback_handler(self, callback: Callable):
        """
        Register a callback to handle suggestion feedback
        
        Args:
            callback: Function to call when feedback is received
        """
        self.register_callback('suggestion_feedback', callback)
        self.logger.info("Registered suggestion feedback handler")