#!/usr/bin/env python3
"""
Enhanced Overlay Bridge Server
- Connects to the eye widget overlay
- Integrates with memory system
- Handles context tracking
- Acts as message broker between frontend and backend
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Set, List, Optional, Callable

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - [BRIDGE] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'overlay_bridge.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('overlay_bridge')

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Ensure memory directory exists
MEMORY_DIR = Path('memory')
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
DEFAULT_FRONTEND_PORT = 8765  # For overlay widget
DEFAULT_BACKEND_PORT = 8766   # For AI engine
MEMORY_FILE = MEMORY_DIR / 'conversation_history.json'
CONTEXT_FILE = MEMORY_DIR / 'temporal_context.json'
LAST_CONTEXT_FILE = MEMORY_DIR / 'last_context.json'

class OverlayBridgeServer:
    """
    Enhanced bridge server for eye widget overlay.
    
    Features:
    - WebSocket server for frontend (overlay) and backend (AI engine)
    - Memory integration for conversation persistence
    - Context tracking and synchronization
    - Robust error handling and logging
    - Heartbeat mechanism for connection monitoring
    """
    
    def __init__(
        self, 
        frontend_port: int = DEFAULT_FRONTEND_PORT, 
        backend_port: int = DEFAULT_BACKEND_PORT,
        memory_enabled: bool = True
    ):
        """Initialize the overlay bridge server."""
        self.frontend_port = frontend_port
        self.backend_port = backend_port
        self.memory_enabled = memory_enabled
        
        # Client tracking
        self.frontend_clients: Set[WebSocketServerProtocol] = set()
        self.backend_clients: Set[WebSocketServerProtocol] = set()
        self.client_info: Dict[str, Dict[str, Any]] = {}
        
        # State tracking
        self.running = False
        self.servers = []
        self.context_data = {}
        self.last_context_update = 0
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.default_conversation_id = str(uuid.uuid4())
        
        # Handler registry
        self.message_handlers = {
            'connection_established': self._handle_connection,
            'user_interaction': self._handle_user_interaction,
            'context_request': self._handle_context_request,
            'memory_store': self._handle_memory_store,
            'clear_conversation': self._handle_clear_conversation,
            'ping': self._handle_ping,
        }
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'connections': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    async def start(self):
        """Start the bridge server."""
        if self.running:
            logger.warning("Bridge server already running")
            return
        
        self.running = True
        logger.info(f"Starting Overlay Bridge Server on ports: frontend={self.frontend_port}, backend={self.backend_port}")
        
        # Load existing context and conversation history if available
        await self._load_context()
        await self._load_conversation_history()
        
        try:
            # Define paths
            frontend_paths = {'/': self._handle_frontend_client}
            backend_paths = {'/': self._handle_backend_client}
            
            # Start frontend (overlay) server
            frontend_server = await websockets.serve(
                self._handle_frontend_client,
                "localhost",
                self.frontend_port
            )
            self.servers.append(frontend_server)
            
            # Start backend (AI engine) server
            backend_server = await websockets.serve(
                self._handle_backend_client,
                "localhost",
                self.backend_port
            )
            self.servers.append(backend_server)
            
            logger.info(f"✅ Overlay Bridge Server running successfully")
            logger.info(f"  - Frontend (overlay) endpoint: ws://localhost:{self.frontend_port}")
            logger.info(f"  - Backend (AI engine) endpoint: ws://localhost:{self.backend_port}")
            
            # Start background tasks
            self.tasks = [
                asyncio.create_task(self._context_monitor()),
                asyncio.create_task(self._periodic_status()),
                asyncio.create_task(self._heartbeat()),
            ]
            
            # Keep running until stopped
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Error starting bridge server: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the bridge server gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping Overlay Bridge Server")
        self.running = False
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
            
        # Close all client connections
        close_tasks = []
        
        for client in self.frontend_clients:
            try:
                close_tasks.append(client.close())
            except Exception as e:
                logger.error(f"Error closing frontend client: {e}")
        
        for client in self.backend_clients:
            try:
                close_tasks.append(client.close())
            except Exception as e:
                logger.error(f"Error closing backend client: {e}")
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Save conversation history
        await self._save_conversation_history()
        
        # Log runtime statistics
        runtime = time.time() - self.stats['start_time']
        logger.info(f"Overlay Bridge Server stopped after running for {runtime:.1f} seconds")
        logger.info(f"Stats: {self.stats}")
    
    async def _handle_frontend_client(self, websocket, path=None):
        """Handle connections from frontend (overlay) clients."""
        client_id = str(uuid.uuid4())
        
        try:
            # Add client to tracking
            self.frontend_clients.add(websocket)
            self.client_info[client_id] = {
                'type': 'frontend',
                'connected_at': time.time(),
                'last_activity': time.time(),
                'client_type': 'unknown',
                'version': 'unknown',
                'capabilities': []
            }
            self.stats['connections'] += 1
            
            logger.info(f"Frontend client connected: {client_id} (total: {len(self.frontend_clients)})")
            
            # Send welcome message
            await self._send_to_client(websocket, 'connection_status', {
                'state': 'connected',
                'server_time': time.time(),
                'client_id': client_id
            })
            
            # Send initial context if available
            if self.context_data:
                await self._send_to_client(websocket, 'context_update', {
                    'available': True,
                    'summary': self.context_data.get('summary', 'Context available'),
                    'timestamp': time.time()
                })
            
            # Send memory status
            await self._send_to_client(websocket, 'memory_status', {
                'connected': self.memory_enabled,
                'last_saved': time.time() if self.memory_enabled else None
            })
            
            # Process messages
            async for message in websocket:
                try:
                    self.stats['messages_received'] += 1
                    self.client_info[client_id]['last_activity'] = time.time()
                    
                    data = json.loads(message)
                    message_type = data.get('type')
                    payload = data.get('payload', {})
                    
                    logger.debug(f"Received frontend message: {message_type}")
                    
                    # Update client info if this is a connection message
                    if message_type == 'connection_established':
                        self.client_info[client_id]['client_type'] = payload.get('client', 'unknown')
                        self.client_info[client_id]['version'] = payload.get('version', 'unknown')
                        self.client_info[client_id]['capabilities'] = payload.get('capabilities', [])
                    
                    # Process with appropriate handler
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](websocket, payload, source='frontend', client_id=client_id)
                    else:
                        # Forward to backend
                        await self._broadcast_to_backends(data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from frontend client")
                    self.stats['errors'] += 1
                except Exception as e:
                    logger.error(f"Error processing frontend message: {e}")
                    self.stats['errors'] += 1
        
        except ConnectionClosed:
            logger.info(f"Frontend client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Unexpected error with frontend client: {e}")
            self.stats['errors'] += 1
        finally:
            self.frontend_clients.discard(websocket)
            if client_id in self.client_info:
                del self.client_info[client_id]
            logger.info(f"Frontend client removed: {client_id} (remaining: {len(self.frontend_clients)})")
    
    async def _handle_backend_client(self, websocket, path=None):
        """Handle connections from backend (AI engine) clients."""
        client_id = str(uuid.uuid4())
        
        try:
            # Add client to tracking
            self.backend_clients.add(websocket)
            self.client_info[client_id] = {
                'type': 'backend',
                'connected_at': time.time(),
                'last_activity': time.time(),
                'client_type': 'unknown',
                'version': 'unknown'
            }
            self.stats['connections'] += 1
            
            logger.info(f"Backend client connected: {client_id} (total: {len(self.backend_clients)})")
            
            # Send welcome message
            await self._send_to_client(websocket, 'connection_status', {
                'state': 'connected',
                'server_time': time.time(),
                'client_id': client_id
            })
            
            # Process messages
            async for message in websocket:
                try:
                    self.stats['messages_received'] += 1
                    self.client_info[client_id]['last_activity'] = time.time()
                    
                    data = json.loads(message)
                    message_type = data.get('type')
                    payload = data.get('payload', {})
                    
                    logger.debug(f"Received backend message: {message_type}")
                    
                    # Process system messages
                    if message_type == 'query_response':
                        # Add to conversation history
                        conversation_id = payload.get('conversation_id', self.default_conversation_id)
                        if self.memory_enabled:
                            await self._add_to_conversation(conversation_id, 'assistant', payload.get('response', ''))
                        
                        # Forward response to all frontend clients
                        await self._broadcast_to_frontends(data)
                    
                    elif message_type == 'context_update':
                        # Update internal context
                        self.context_data = payload
                        self.last_context_update = time.time()
                        
                        # Save to context files
                        await self._save_context()
                        
                        # Forward to all frontend clients
                        await self._broadcast_to_frontends(data)
                    
                    else:
                        # Forward other messages to frontends
                        await self._broadcast_to_frontends(data)
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from backend client")
                    self.stats['errors'] += 1
                except Exception as e:
                    logger.error(f"Error processing backend message: {e}")
                    self.stats['errors'] += 1
        
        except ConnectionClosed:
            logger.info(f"Backend client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Unexpected error with backend client: {e}")
            self.stats['errors'] += 1
        finally:
            self.backend_clients.discard(websocket)
            if client_id in self.client_info:
                del self.client_info[client_id]
            logger.info(f"Backend client removed: {client_id} (remaining: {len(self.backend_clients)})")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle client connection message."""
        client_type = payload.get('client', 'unknown')
        version = payload.get('version', 'unknown')
        capabilities = payload.get('capabilities', [])
        
        logger.info(f"Client identified: {client_type} v{version} with capabilities: {capabilities}")
        
        # Update client info
        if client_id in self.client_info:
            self.client_info[client_id]['client_type'] = client_type
            self.client_info[client_id]['version'] = version
            self.client_info[client_id]['capabilities'] = capabilities
        
        # Acknowledge connection
        await self._send_to_client(websocket, 'connection_acknowledged', {
            'server_version': '2.0.0',
            'server_time': time.time(),
            'features': ['memory', 'context_tracking', 'chat']
        })
    
    async def _handle_user_interaction(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle user interaction message."""
        interaction_type = payload.get('type')
        
        if interaction_type == 'query':
            query = payload.get('query', '')
            conversation_id = payload.get('conversation_id', self.default_conversation_id)
            
            logger.info(f"Received user query: {query[:50]}{'...' if len(query) > 50 else ''}")
            
            # Add to conversation history
            if self.memory_enabled:
                await self._add_to_conversation(conversation_id, 'user', query)
            
            # Check if we have backend clients
            if not self.backend_clients:
                # No backend available, respond directly
                await self._send_to_client(websocket, 'query_response', {
                    'response': "I'm sorry, but I cannot process your request at the moment as I'm not connected to the AI engine. Please try again later.",
                    'request_id': payload.get('request_id'),
                    'conversation_id': conversation_id,
                    'error': 'NO_BACKEND_CONNECTION'
                })
                return
            
            # Add context to payload if available
            if self.context_data:
                payload['context'] = {
                    'summary': self.context_data.get('summary', ''),
                    'active_app': self.context_data.get('active_app', ''),
                    'active_window': self.context_data.get('active_window', '')
                }
            
            # Forward to backend clients
            await self._broadcast_to_backends({
                'type': 'user_interaction',
                'payload': payload
            })
    
    async def _handle_context_request(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle context request message."""
        if self.context_data:
            await self._send_to_client(websocket, 'context_update', {
                'available': True,
                'summary': self.context_data.get('summary', 'Context available'),
                'active_app': self.context_data.get('active_app', ''),
                'timestamp': time.time()
            })
        else:
            await self._send_to_client(websocket, 'context_update', {
                'available': False,
                'timestamp': time.time()
            })
    
    async def _handle_memory_store(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle memory storage request."""
        if not self.memory_enabled:
            await self._send_to_client(websocket, 'memory_status', {
                'connected': False,
                'error': 'Memory storage is disabled',
                'success': False
            })
            return
            
        try:
            conversation = payload.get('conversation', [])
            if not conversation:
                return
            
            # Get conversation ID from payload or use client ID
            conversation_id = payload.get('conversation_id', client_id)
            
            # Update conversation history
            self.conversations[conversation_id] = conversation
            
            # Save to disk
            await self._save_conversation_history()
            
            # Acknowledge storage
            await self._send_to_client(websocket, 'memory_status', {
                'connected': True,
                'last_saved': time.time(),
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            self.stats['errors'] += 1
            await self._send_to_client(websocket, 'memory_status', {
                'connected': False,
                'error': str(e),
                'success': False
            })
    
    async def _handle_clear_conversation(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle conversation clear request."""
        conversation_id = payload.get('conversation_id', client_id)
        
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        
        # Create clear marker in memory
        await self._save_conversation_history()
        
        # Acknowledge
        await self._send_to_client(websocket, 'conversation_cleared', {
            'success': True,
            'timestamp': time.time()
        })
    
    async def _handle_ping(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str, client_id: str):
        """Handle ping message with a pong response."""
        await self._send_to_client(websocket, 'pong', {
            'timestamp': time.time(),
            'echo': payload.get('timestamp', 0)
        })
    
    async def _add_to_conversation(self, conversation_id: str, role: str, content: str):
        """Add a message to the conversation history."""
        if not self.memory_enabled:
            return
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        self.conversations[conversation_id].append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        
        # Save after each addition
        await self._save_conversation_history()
    
    async def _broadcast_to_frontends(self, message: Dict[str, Any]):
        """Broadcast a message to all frontend clients."""
        if not self.frontend_clients:
            return
        
        self.stats['messages_sent'] += len(self.frontend_clients)
        message_json = json.dumps(message)
        
        await asyncio.gather(
            *[client.send(message_json) for client in self.frontend_clients],
            return_exceptions=True
        )
    
    async def _broadcast_to_backends(self, message: Dict[str, Any]):
        """Broadcast a message to all backend clients."""
        if not self.backend_clients:
            return
        
        self.stats['messages_sent'] += len(self.backend_clients)
        message_json = json.dumps(message)
        
        await asyncio.gather(
            *[client.send(message_json) for client in self.backend_clients],
            return_exceptions=True
        )
    
    async def _send_to_client(self, websocket: WebSocketServerProtocol, message_type: str, payload: Dict[str, Any]):
        """Send a message to a specific client."""
        try:
            message = {
                'type': message_type,
                'payload': payload
            }
            self.stats['messages_sent'] += 1
            await websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _context_monitor(self):
        """Monitor for context changes and update clients."""
        while self.running:
            try:
                # Check for context file updates
                if CONTEXT_FILE.exists():
                    file_mtime = CONTEXT_FILE.stat().st_mtime
                    current_time = time.time()
                    
                    # Only reload if file is recent (newer than our last update)
                    if file_mtime > self.last_context_update:
                        await self._load_context()
                        
                        # Notify clients of the update
                        if self.context_data and self.frontend_clients:
                            await self._broadcast_to_frontends({
                                'type': 'context_update',
                                'payload': {
                                    'available': True,
                                    'summary': self.context_data.get('summary', 'Context updated'),
                                    'active_app': self.context_data.get('active_app', ''),
                                    'timestamp': time.time()
                                }
                            })
            except Exception as e:
                logger.error(f"Error in context monitor: {e}")
                self.stats['errors'] += 1
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    async def _heartbeat(self):
        """Send periodic heartbeats to connected clients."""
        while self.running:
            try:
                heartbeat = {
                    'type': 'heartbeat',
                    'payload': {
                        'timestamp': time.time(),
                        'uptime': time.time() - self.stats['start_time'],
                        'frontend_clients': len(self.frontend_clients),
                        'backend_clients': len(self.backend_clients)
                    }
                }
                
                if self.frontend_clients:
                    await self._broadcast_to_frontends(heartbeat)
                if self.backend_clients:
                    await self._broadcast_to_backends(heartbeat)
                
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
                self.stats['errors'] += 1
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    async def _periodic_status(self):
        """Log periodic status updates."""
        while self.running:
            try:
                uptime = time.time() - self.stats['start_time']
                logger.info(f"Status update - Uptime: {uptime:.1f}s, Frontend clients: {len(self.frontend_clients)}, " 
                           f"Backend clients: {len(self.backend_clients)}, Messages: {self.stats['messages_received']}/" 
                           f"{self.stats['messages_sent']}, Errors: {self.stats['errors']}")
            except Exception as e:
                logger.error(f"Error in status update: {e}")
            
            await asyncio.sleep(60)  # Update every minute
    
    async def _load_context(self):
        """Load context data from file."""
        try:
            if CONTEXT_FILE.exists():
                with open(CONTEXT_FILE, 'r') as f:
                    data = json.load(f)
                    if data:
                        self.context_data = data
                        self.last_context_update = time.time()
                        logger.info(f"Loaded context data: {self.context_data.get('summary', 'No summary')}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _save_context(self):
        """Save context data to files."""
        try:
            if self.context_data:
                # Save to context file
                with open(CONTEXT_FILE, 'w') as f:
                    json.dump(self.context_data, f)
                
                # Also save to last_context file for other components
                with open(LAST_CONTEXT_FILE, 'w') as f:
                    json.dump(self.context_data, f)
                    
                logger.debug(f"Saved context data to files")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _load_conversation_history(self):
        """Load conversation history from file."""
        if not self.memory_enabled:
            return False
            
        try:
            if MEMORY_FILE.exists():
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.conversations = data
                        logger.info(f"Loaded conversation history: {len(self.conversations)} conversations")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _save_conversation_history(self):
        """Save conversation history to file."""
        if not self.memory_enabled:
            return False
            
        try:
            # Make sure memory directory exists
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save conversations to file
            with open(MEMORY_FILE, 'w') as f:
                json.dump(self.conversations, f)
                
            logger.debug(f"Saved conversation history: {len(self.conversations)} conversations")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
            self.stats['errors'] += 1
            return False


def signal_handler(sig, frame):
    """Handle interrupt signals."""
    logger.info("Shutdown signal received")
    if 'server' in globals() and server.running:
        asyncio.run(server.stop())
    sys.exit(0)


async def main():
    """Main entry point."""
    global server
    
    try:
        # Create and start server
        server = OverlayBridgeServer()
        await server.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        if 'server' in globals() and server.running:
            await server.stop()


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print startup banner
    print("\n=== Enhanced Overlay Bridge Server ===")
    print("Connecting your eye widget overlay with AI and memory systems")
    print(f"Frontend port: {DEFAULT_FRONTEND_PORT}, Backend port: {DEFAULT_BACKEND_PORT}")
    print("Press Ctrl+C to exit\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)