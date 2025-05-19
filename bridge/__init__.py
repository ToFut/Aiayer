"""
Bridge package for WebSocket communication between components.
"""

from .message_bridge import MessageBridge, Message, MessageType, MessagePriority
from .client import BridgeClient
from .server import BridgeServer

# Alias for backward compatibility
Bridge = MessageBridge

__all__ = [
    'MessageBridge',
    'Message',
    'MessageType',
    'MessagePriority',
    'BridgeClient',
    'BridgeServer',
    'Bridge'
] 