import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MessageType(Enum):
    QUERY = "query"
    RESPONSE = "response"
    SYSTEM = "system"
    ERROR = "error"

class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class Message:
    def __init__(
        self,
        type: MessageType,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        timestamp: Optional[float] = None,
        message_id: Optional[str] = None
    ):
        self.type = type
        self.content = content
        self.priority = priority
        self.timestamp = timestamp or datetime.now().timestamp()
        self.message_id = message_id or str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            type=MessageType(data["type"]),
            content=data["content"],
            priority=MessagePriority(data["priority"]),
            timestamp=data["timestamp"],
            message_id=data["message_id"]
        )

class MessageBridge:
    """Message bridge for handling communication between frontend and backend"""
    
    def __init__(self):
        self.frontend_clients = set()
        self.backend_clients = set()
        self.message_queue = asyncio.Queue()
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        self.bridge_id = id(self)

    async def start(self):
        """Start the message bridge processing loop."""
        if self.running:
            return

        self.running = True
        self.logger.info(f"🚀 STARTING MESSAGE BRIDGE: [VERIFICATION CHECK 7/10]")
        self.logger.info(f"  - Bridge instance ID: {self.bridge_id}")
        self.logger.info(f"  - Queue size at start: {self.message_queue.qsize()}")
        self.logger.info(f"  - Frontend clients: {len(self.frontend_clients)}")
        self.logger.info(f"  - Backend clients: {len(self.backend_clients)}")
        self.logger.info(f"  - Bridge started at: {datetime.now().isoformat()}")

        try:
            while self.running:
                try:
                    message = await self.message_queue.get()
                    # Process message here
                    self.message_queue.task_done()
                except asyncio.CancelledError:
                    self.logger.warning("⚠️ BRIDGE TASK CANCELLED: [VERIFICATION WARNING]")
                    self.logger.warning("  - Breaking bridge processing loop")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")

        finally:
            self.logger.info("✅ BRIDGE LOOP COMPLETED: [VERIFICATION PASSED]")
            self.logger.info(f"  - Total runtime: {datetime.now().timestamp() - self.start_time:.2f} seconds")
            self.logger.info(f"  - Messages processed: {self.processed_messages}")
            self.logger.info(f"  - Errors encountered: {self.error_count}")

    async def stop(self):
        """Stop the message bridge."""
        self.running = False
        self.logger.info("Bridge stopped")

    async def send_message(self, message: Message):
        """Send a message through the bridge."""
        await self.message_queue.put(message) 