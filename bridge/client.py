import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
import websockets
from .message_bridge import Message, MessageType, MessagePriority
from collections import deque
import time

logger = logging.getLogger(__name__)

class BridgeClient:
    def __init__(self, host: str = "localhost", port: int = 8765, path: str = "/frontend"):
        self.host = host
        self.port = port
        self.path = path
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
        self.message_queue = deque()
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 30.0
        self.reconnect_attempts = 0
        self.last_heartbeat = 0
        self.heartbeat_interval = 30
        self.running = False

    async def connect(self):
        """Connect to the bridge server with automatic reconnection."""
        self.running = True
        while self.running:
            try:
                uri = f"ws://{self.host}:{self.port}{self.path}"
                self.websocket = await websockets.connect(uri)
                self.connected = True
                self.reconnect_attempts = 0
                self.last_heartbeat = time.time()
                self.logger.info(f"Connected to bridge server at {uri}")
                
                # Start message handling and heartbeat tasks
                asyncio.create_task(self._handle_messages())
                asyncio.create_task(self._heartbeat())
                asyncio.create_task(self._process_message_queue())
                
                # Wait for connection to close
                await self.websocket.wait_closed()
                
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self.connected = False
                
            if self.running:
                # Exponential backoff for reconnection
                delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), self.max_reconnect_delay)
                self.reconnect_attempts += 1
                self.logger.info(f"Reconnecting in {delay} seconds...")
                await asyncio.sleep(delay)

    async def disconnect(self):
        """Disconnect from the bridge server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("Disconnected from bridge server")

    async def send(self, message_type: str, content: Any, priority: MessagePriority = MessagePriority.NORMAL):
        """Send a message to the bridge server with queuing support."""
        message = Message(
            type=MessageType(message_type),
            content=content,
            priority=priority
        )
        
        if not self.connected:
            # Queue message for later sending
            self.message_queue.append(message)
            self.logger.debug(f"Message queued: {message_type}")
            return
        
        try:
            await self._send_message(message)
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            # Queue message for retry
            self.message_queue.append(message)
            self.connected = False

    async def _send_message(self, message: Message):
        """Internal method to send a message."""
        if not self.websocket:
            raise ConnectionError("No WebSocket connection")
        
        try:
            await self.websocket.send(json.dumps(message.to_dict()))
            self.last_heartbeat = time.time()
        except Exception as e:
            self.logger.error(f"Error in _send_message: {e}")
            raise

    async def _process_message_queue(self):
        """Process queued messages when connection is available."""
        while self.running:
            if self.connected and self.message_queue:
                message = self.message_queue.popleft()
                try:
                    await self._send_message(message)
                except Exception as e:
                    self.logger.error(f"Error processing queued message: {e}")
                    self.message_queue.appendleft(message)
                    self.connected = False
            await asyncio.sleep(0.1)

    async def _heartbeat(self):
        """Send periodic heartbeat to keep connection alive."""
        while self.running and self.connected:
            try:
                if time.time() - self.last_heartbeat > self.heartbeat_interval:
                    await self._send_message(Message(
                        type=MessageType.HEARTBEAT,
                        content={"timestamp": time.time()},
                        priority=MessagePriority.LOW
                    ))
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                self.connected = False
            await asyncio.sleep(self.heartbeat_interval)

    def on(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler

    async def _handle_messages(self):
        """Handle incoming messages from the bridge server."""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "heartbeat":
                        self.last_heartbeat = time.time()
                        continue
                    
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](data.get("content"))
                    else:
                        self.logger.warning(f"No handler registered for message type: {message_type}")
                        
                except json.JSONDecodeError:
                    self.logger.error("Invalid JSON received")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Connection to bridge server closed")
            self.connected = False
        except Exception as e:
            self.logger.error(f"Error in message handling loop: {e}")
            self.connected = False 