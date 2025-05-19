#!/usr/bin/env python3
"""
Advanced Bridge Server
Connects the frontend overlay with AI backend and memory systems.
"""
import asyncio
import json
import logging
import uuid
import os
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Set, List, Optional

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - [BRIDGE] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'bridge.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('advanced_bridge')

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

MEMORY_DIR = Path('memory')
MEMORY_FILE = MEMORY_DIR / 'last_context.json'
CONTEXT_FILE = MEMORY_DIR / 'temporal_context.json'

# Ensure memory directory exists
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

class AdvancedBridge:
    """
    Advanced bridge server that connects the frontend overlay with AI backend and memory.
    Features:
    - WebSocket communication with frontend
    - Connection to backend systems
    - Memory integration for conversation persistence
    - Context tracking and management
    - Robust error handling and reconnection
    """
    
    def __init__(self, frontend_port=8765, backend_port=8766):
        """Initialize the bridge with port configurations."""
        self.frontend_port = frontend_port
        self.backend_port = backend_port
        self.frontend_clients: Set[WebSocketServerProtocol] = set()
        self.backend_clients: Set[WebSocketServerProtocol] = set()
        self.running = False
        self.context_data: Dict[str, Any] = {}
        self.memory_available = True
        self.memory_last_saved = None
        self.context_available = False
        self.message_handlers = {
            'connection_established': self.handle_connection,
            'user_interaction': self.handle_user_interaction,
            'context_request': self.handle_context_request,
            'memory_store': self.handle_memory_store,
            'clear_conversation': self.handle_clear_conversation
        }
        self.server = None
    
    async def start(self):
        """Start the bridge server."""
        if self.running:
            logger.warning("Bridge already running")
            return
        
        self.running = True
        logger.info(f"Starting Advanced Bridge on ports: frontend={self.frontend_port}, backend={self.backend_port}")
        
        # Load existing context if available
        await self.load_context()
        
        # Create tasks
        try:
            # Start frontend and backend servers
            frontend_server = await websockets.serve(
                self.handle_frontend_client,
                "localhost",
                self.frontend_port
            )
            
            backend_server = await websockets.serve(
                self.handle_backend_client,
                "localhost",
                self.backend_port
            )
            
            self.server = frontend_server
            
            logger.info(f"✅ Advanced Bridge running successfully")
            logger.info(f"  - Frontend endpoint: ws://localhost:{self.frontend_port}")
            logger.info(f"  - Backend endpoint: ws://localhost:{self.backend_port}")
            
            # Create background tasks
            context_update_task = asyncio.create_task(self.context_update_loop())
            heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            
            # Keep the server running
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Error starting bridge server: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the bridge server gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping Advanced Bridge")
        self.running = False
        
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
        
        logger.info("Advanced Bridge stopped")
    
    async def handle_frontend_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle connection from a frontend client."""
        try:
            client_id = str(uuid.uuid4())
            self.frontend_clients.add(websocket)
            
            logger.info(f"Frontend client connected: {client_id} (total: {len(self.frontend_clients)})")
            
            # Send welcome message
            await self.send_to_client(websocket, 'connection_status', {
                'state': 'connected',
                'server_time': time.time(),
                'client_id': client_id
            })
            
            # Send initial context if available
            if self.context_data:
                await self.send_to_client(websocket, 'context_update', {
                    'available': True,
                    'summary': self.context_data.get('summary', 'Context available'),
                    'timestamp': time.time()
                })
            
            # Send memory status
            await self.send_to_client(websocket, 'memory_status', {
                'connected': self.memory_available,
                'last_saved': self.memory_last_saved
            })
            
            # Process messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    payload = data.get('payload', {})
                    
                    logger.info(f"Received frontend message: {message_type}")
                    
                    # Process with appropriate handler
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](websocket, payload, source='frontend')
                    else:
                        # Forward to backend
                        await self.broadcast_to_backends(data)
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from frontend client")
                except Exception as e:
                    logger.error(f"Error processing frontend message: {e}")
        
        except ConnectionClosed:
            logger.info(f"Frontend client disconnected")
        except Exception as e:
            logger.error(f"Unexpected error with frontend client: {e}")
        finally:
            self.frontend_clients.discard(websocket)
            logger.info(f"Frontend client removed (remaining: {len(self.frontend_clients)})")
    
    async def handle_backend_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle connection from a backend client."""
        try:
            client_id = str(uuid.uuid4())
            self.backend_clients.add(websocket)
            
            logger.info(f"Backend client connected: {client_id} (total: {len(self.backend_clients)})")
            
            # Send welcome message
            await self.send_to_client(websocket, 'connection_status', {
                'state': 'connected',
                'server_time': time.time(),
                'client_id': client_id
            })
            
            # Process messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    payload = data.get('payload', {})
                    
                    logger.info(f"Received backend message: {message_type}")
                    
                    # Process system messages
                    if message_type == 'query_response':
                        # Forward response to all frontend clients
                        await self.broadcast_to_frontends(data)
                        
                        # Store in memory
                        await self.save_to_memory(data)
                    
                    elif message_type == 'context_update':
                        # Update internal context
                        self.context_data = payload
                        self.context_available = True
                        
                        # Forward to all frontend clients
                        await self.broadcast_to_frontends(data)
                        
                        # Save to context file
                        await self.save_context()
                    
                    else:
                        # Forward other messages to frontends
                        await self.broadcast_to_frontends(data)
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from backend client")
                except Exception as e:
                    logger.error(f"Error processing backend message: {e}")
        
        except ConnectionClosed:
            logger.info(f"Backend client disconnected")
        except Exception as e:
            logger.error(f"Unexpected error with backend client: {e}")
        finally:
            self.backend_clients.discard(websocket)
            logger.info(f"Backend client removed (remaining: {len(self.backend_clients)})")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str):
        """Handle client connection message."""
        client_type = payload.get('client', 'unknown')
        version = payload.get('version', 'unknown')
        capabilities = payload.get('capabilities', [])
        
        logger.info(f"Client identified: {client_type}, version: {version}, capabilities: {capabilities}")
        
        # Acknowledge connection
        await self.send_to_client(websocket, 'connection_acknowledged', {
            'server_version': '1.0.0',
            'server_time': time.time(),
            'features': ['memory', 'context_tracking', 'chat']
        })
    
    async def handle_user_interaction(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str):
        """Handle user interaction message."""
        interaction_type = payload.get('type')
        
        if interaction_type == 'query':
            query = payload.get('query', '')
            logger.info(f"Received user query: {query[:50]}{'...' if len(query) > 50 else ''}")
            
            # Check if we have backend clients
            if not self.backend_clients:
                # No backend available, respond directly
                await self.send_to_client(websocket, 'query_response', {
                    'response': "I'm sorry, but I cannot process your request at the moment as I'm not connected to the backend AI system. Please try again later.",
                    'request_id': payload.get('request_id'),
                    'conversation_id': payload.get('conversation_id'),
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
            await self.broadcast_to_backends({
                'type': 'user_interaction',
                'payload': payload
            })
    
    async def handle_context_request(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str):
        """Handle context request message."""
        if self.context_data:
            await self.send_to_client(websocket, 'context_update', {
                'available': True,
                'summary': self.context_data.get('summary', 'Context available'),
                'active_app': self.context_data.get('active_app', ''),
                'timestamp': time.time()
            })
        else:
            await self.send_to_client(websocket, 'context_update', {
                'available': False,
                'timestamp': time.time()
            })
    
    async def handle_memory_store(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str):
        """Handle memory storage request."""
        try:
            conversation = payload.get('conversation', [])
            if not conversation:
                return
            
            # Create memory entry
            memory_data = {
                'conversation': conversation,
                'timestamp': time.time(),
                'context': self.context_data
            }
            
            # Save to memory file
            await self.save_to_memory(memory_data)
            
            # Acknowledge storage
            await self.send_to_client(websocket, 'memory_status', {
                'connected': self.memory_available,
                'last_saved': self.memory_last_saved,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            await self.send_to_client(websocket, 'memory_status', {
                'connected': False,
                'error': str(e),
                'success': False
            })
    
    async def handle_clear_conversation(self, websocket: WebSocketServerProtocol, payload: Dict[str, Any], source: str):
        """Handle conversation clear request."""
        # Create clear marker in memory
        memory_data = {
            'conversation_cleared': True,
            'timestamp': time.time()
        }
        
        # Save marker to memory
        await self.save_to_memory(memory_data)
        
        # Acknowledge
        await self.send_to_client(websocket, 'conversation_cleared', {
            'success': True,
            'timestamp': time.time()
        })
    
    async def broadcast_to_frontends(self, message: Dict[str, Any]):
        """Broadcast a message to all frontend clients."""
        if not self.frontend_clients:
            return
        
        message_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_json) for client in self.frontend_clients],
            return_exceptions=True
        )
    
    async def broadcast_to_backends(self, message: Dict[str, Any]):
        """Broadcast a message to all backend clients."""
        if not self.backend_clients:
            return
        
        message_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_json) for client in self.backend_clients],
            return_exceptions=True
        )
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message_type: str, payload: Dict[str, Any]):
        """Send a message to a specific client."""
        try:
            message = {
                'type': message_type,
                'payload': payload
            }
            await websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            return False
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats to connected clients."""
        while self.running:
            try:
                heartbeat = {
                    'type': 'heartbeat',
                    'payload': {
                        'timestamp': time.time(),
                        'frontend_clients': len(self.frontend_clients),
                        'backend_clients': len(self.backend_clients)
                    }
                }
                
                if self.frontend_clients:
                    await self.broadcast_to_frontends(heartbeat)
                if self.backend_clients:
                    await self.broadcast_to_backends(heartbeat)
                
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    async def context_update_loop(self):
        """Periodically check for context updates."""
        while self.running:
            try:
                # Check if context file exists and is newer than our data
                if CONTEXT_FILE.exists():
                    file_mtime = CONTEXT_FILE.stat().st_mtime
                    current_time = time.time()
                    
                    # Only reload if file is recent (within the last minute)
                    if current_time - file_mtime < 60:
                        await self.load_context()
            except Exception as e:
                logger.error(f"Error in context update loop: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def load_context(self):
        """Load context data from file."""
        try:
            if CONTEXT_FILE.exists():
                with open(CONTEXT_FILE, 'r') as f:
                    data = json.load(f)
                    if data:
                        self.context_data = data
                        self.context_available = True
                        logger.info(f"Loaded context data: {self.context_data.get('summary', 'No summary')}")
                    else:
                        self.context_available = False
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            self.context_available = False
    
    async def save_context(self):
        """Save context data to file."""
        try:
            if self.context_data:
                with open(CONTEXT_FILE, 'w') as f:
                    json.dump(self.context_data, f)
                logger.info(f"Saved context data to file")
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    async def save_to_memory(self, data: Dict[str, Any]):
        """Save data to memory file."""
        try:
            # Create memory entry
            memory_entry = {
                'timestamp': time.time(),
                'data': data
            }
            
            # Make sure memory directory exists
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            
            # Create last context file if it doesn't exist
            if not MEMORY_FILE.exists():
                with open(MEMORY_FILE, 'w') as f:
                    json.dump([], f)
            
            # Read existing memory
            try:
                with open(MEMORY_FILE, 'r') as f:
                    memory = json.load(f)
                    if not isinstance(memory, list):
                        memory = []
            except Exception:
                memory = []
            
            # Add new entry
            memory.append(memory_entry)
            
            # Keep only last 100 entries
            if len(memory) > 100:
                memory = memory[-100:]
            
            # Write back
            with open(MEMORY_FILE, 'w') as f:
                json.dump(memory, f)
            
            self.memory_last_saved = time.time()
            self.memory_available = True
            
            logger.info(f"Saved data to memory")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")
            self.memory_available = False
            return False

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    logger.info("Shutdown signal received")
    if 'bridge' in globals() and bridge.running:
        asyncio.run(bridge.stop())
    sys.exit(0)

async def main():
    """Main entry point."""
    global bridge
    
    try:
        # Create and start bridge
        bridge = AdvancedBridge()
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        if 'bridge' in globals() and bridge.running:
            await bridge.stop()

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print startup banner
    print("\n=== Advanced AI Bridge Server ===")
    print("Connecting your overlay with AI and memory systems")
    print(f"Frontend port: 8765, Backend port: 8766")
    print("Press Ctrl+C to exit\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)