import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
import websockets
from .message_bridge import Message, MessageType, MessagePriority

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

    async def connect(self):
        """Connect to the bridge server."""
        try:
            uri = f"ws://{self.host}:{self.port}{self.path}"
            self.websocket = await websockets.connect(uri)
            self.connected = True
            self.logger.info(f"Connected to bridge server at {uri}")
            
            # Start message handling loop
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            self.logger.error(f"Failed to connect to bridge server: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the bridge server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("Disconnected from bridge server")

    async def send(self, message_type: str, content: Any, priority: MessagePriority = MessagePriority.NORMAL):
        """Send a message to the bridge server."""
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to bridge server")

        message = Message(
            type=MessageType(message_type),
            content=content,
            priority=priority
        )
        
        try:
            await self.websocket.send(json.dumps(message.to_dict()))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            raise

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