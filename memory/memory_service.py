#!/usr/bin/env python3
"""
Memory Service
Handles memory operations and WebSocket communication with the bridge server.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryService:
    """Memory service that handles memory operations and WebSocket communication."""
    
    def __init__(self, server_uri: str = "ws://127.0.0.1:8765"):
        self.server_uri = server_uri
        self.ws: Optional[WebSocketClientProtocol] = None
        self.client_id = str(uuid.uuid4())
        self.running = False
        self.reconnect_delay = 3
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
        # Initialize memory system
        from memory.memory_system import MemorySystem
        self.memory_system = MemorySystem()
    
    async def start(self):
        """Start the memory service."""
        try:
            # Initialize memory system
            if not await self.memory_system.initialize():
                logger.error("Failed to initialize memory system")
                return False
            
            # Start WebSocket connection
            self.running = True
            await self._connect()
            return True
        except Exception as e:
            logger.error(f"Error starting memory service: {e}")
            return False
    
    async def stop(self):
        """Stop the memory service."""
        self.running = False
        if self.ws:
            await self.ws.close()
    
    async def _connect(self):
        """Connect to the WebSocket server."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.server_uri}")
                async with websockets.connect(self.server_uri) as websocket:
                    self.ws = websocket
                    self.reconnect_attempts = 0
                    
                    # Send connection message
                    await self._send_connection_message()
                    
                    # Handle messages
                    await self._handle_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            
            if self.running:
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
    
    async def _send_connection_message(self):
        """Send initial connection message to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_type": "memory",
                    "client_id": self.client_id,
                    "version": "1.0.0",
                    "capabilities": ["memory_operations", "context_tracking"],
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent connection message")
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON message received")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message."""
        try:
            msg_type = data.get('type')
            
            if msg_type == 'memory_update':
                # Update memory with new data
                await self._handle_memory_update(data.get('data', {}))
            elif msg_type == 'enhanced_memory_data':
                # Handle enhanced memory data from Total Screen Analyzer
                await self._handle_enhanced_memory_data(data.get('payload', {}))
            elif msg_type == 'context_request':
                # Send current context
                await self._send_context(data.get('data', {}))
            elif msg_type == 'clear_memory':
                # Clear memory
                await self._clear_memory()
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_memory_update(self, data: Dict[str, Any]):
        """Handle memory update message."""
        try:
            # Update memory system
            if 'short_term' in data:
                self.memory_system.short_term_memory.extend(data['short_term'])
            if 'long_term' in data:
                self.memory_system.long_term_memory.extend(data['long_term'])
            if 'context' in data:
                self.memory_system.context_memory.update(data['context'])
            
            # Save memory state
            self.memory_system._save_memory_state()
            
            logger.info("Memory updated successfully")
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
    
    async def _handle_enhanced_memory_data(self, memory_item: Dict[str, Any]):
        """Handle enhanced memory data from Total Screen Analyzer."""
        try:
            priority = memory_item.get('priority', 'medium')
            memory_type = memory_item.get('memory_type', 'short_term')
            content = memory_item.get('content', {})
            
            logger.info(f"Processing enhanced memory item: priority={priority}, type={memory_type}")
            
            # Route to appropriate memory layer based on priority and type
            if memory_type == 'long_term' or priority == 'high':
                # Add to long-term memory for high priority or explicitly long-term items
                if not hasattr(self.memory_system, 'long_term_memory'):
                    self.memory_system.long_term_memory = []
                self.memory_system.long_term_memory.append({
                    'timestamp': datetime.now().isoformat(),
                    'priority': priority,
                    'source': 'total_screen_analyzer',
                    'data': content,
                    'tags': memory_item.get('tags', []),
                    'relationships': memory_item.get('relationships', [])
                })
                
            elif memory_type == 'context' or 'context' in memory_item.get('tags', []):
                # Add to context memory for context-related items
                if not hasattr(self.memory_system, 'context_memory'):
                    self.memory_system.context_memory = {}
                
                # Use application context as key
                app_context = content.get('application_context', {}).get('name', 'unknown_app')
                if app_context not in self.memory_system.context_memory:
                    self.memory_system.context_memory[app_context] = []
                
                self.memory_system.context_memory[app_context].append({
                    'timestamp': datetime.now().isoformat(),
                    'priority': priority,
                    'source': 'total_screen_analyzer',
                    'data': content,
                    'tags': memory_item.get('tags', [])
                })
                
            else:
                # Default to short-term memory
                if not hasattr(self.memory_system, 'short_term_memory'):
                    self.memory_system.short_term_memory = []
                self.memory_system.short_term_memory.append({
                    'timestamp': datetime.now().isoformat(),
                    'priority': priority,
                    'source': 'total_screen_analyzer',
                    'data': content,
                    'tags': memory_item.get('tags', [])
                })
            
            # If this is a high-priority item with insights, also add to conscious memory
            if priority == 'high' and content.get('insights'):
                try:
                    # Update conscious memory with insights
                    if hasattr(self.memory_system, 'conscious_memory') and self.memory_system.conscious_memory:
                        await self.memory_system.conscious_memory.update_conscious_memory(content)
                        logger.info("Updated conscious memory with high-priority insights")
                except Exception as conscious_error:
                    logger.warning(f"Failed to update conscious memory: {conscious_error}")
            
            # Save memory state
            if hasattr(self.memory_system, '_save_memory_state'):
                self.memory_system._save_memory_state()
            
            logger.info(f"Successfully stored enhanced memory item in {memory_type} memory")
            
        except Exception as e:
            logger.error(f"Error handling enhanced memory data: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _send_context(self, request: Dict[str, Any]):
        """Send current context to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "context_update",
                "data": {
                    "short_term": self.memory_system.short_term_memory,
                    "long_term": self.memory_system.long_term_memory,
                    "context": self.memory_system.context_memory,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent context update")
        except Exception as e:
            logger.error(f"Error sending context: {e}")
    
    async def _clear_memory(self):
        """Clear all memory."""
        try:
            self.memory_system.short_term_memory = []
            self.memory_system.long_term_memory = []
            self.memory_system.context_memory = {}
            self.memory_system._save_memory_state()
            logger.info("Memory cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")

async def main():
    """Main function to start the memory service."""
    service = MemoryService()
    if await service.start():
        try:
            # Keep the service running
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        finally:
            await service.stop()
    else:
        logger.error("Failed to start service")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1) 