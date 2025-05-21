#!/usr/bin/env python3
"""
Unified WebSocket Bridge Server
Handles connections between frontend, backend, memory system, and LLM service.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
import time
from datetime import datetime
from typing import Dict, Set, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from collections import defaultdict

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BridgeServer:
    """Unified WebSocket server that manages all system connections."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, Set[WebSocketServerProtocol]] = {
            'frontend': set(),
            'backend': set(),
            'memory': set(),
            'llm': set()
        }
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self.client_heartbeats: Dict[str, float] = {}
        self.message_stats: Dict[str, int] = defaultdict(int)
        self.running = False
        self.server = None
        self.heartbeat_interval = 30
        self.heartbeat_timeout = 60
        self.cleanup_interval = 10
        
    async def start(self):
        """Start the WebSocket server."""
        try:
            self.server = await websockets.serve(
                lambda ws, path: self._handle_client(ws, path),
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            self.running = True
            logger.info(f"Bridge server started on ws://{self.host}:{self.port}")
            
            # Start background tasks
            asyncio.create_task(self._broadcast_status())
            asyncio.create_task(self._cleanup_stale_connections())
            
            return True
        except Exception as e:
            logger.error(f"Error starting bridge server: {e}")
            return False
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("Bridge server stopped")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connections."""
        client_id = str(uuid.uuid4())
        client_type = None
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "data": {
                    "message": "Connected to bridge server",
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    self.message_stats[msg_type] += 1
                    
                    # Update heartbeat
                    self.client_heartbeats[client_id] = time.time()
                    
                    # Handle connection establishment
                    if msg_type == 'connection_established':
                        client_type = data.get('payload', {}).get('client_type', 'unknown')
                        if client_type in self.clients:
                            self.clients[client_type].add(websocket)
                            self.client_info[client_id] = {
                                'type': client_type,
                                'connected_at': datetime.now().isoformat(),
                                'info': data.get('payload', {}),
                                'last_activity': time.time()
                            }
                            logger.info(f"Client {client_id} ({client_type}) connected")
                            
                            # Send server ready message
                            await websocket.send(json.dumps({
                                "type": "server_ready",
                                "data": {
                                    "status": "connected",
                                    "client_id": client_id,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                        else:
                            logger.warning(f"Unknown client type: {client_type}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "data": {
                                    "message": f"Unknown client type: {client_type}",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                    
                    # Handle heartbeat
                    elif msg_type == 'heartbeat':
                        self.client_heartbeats[client_id] = time.time()
                        await websocket.send(json.dumps({
                            "type": "heartbeat_ack",
                            "data": {
                                "timestamp": time.time()
                            }
                        }))
                    
                    # Handle other message types
                    else:
                        # Update last activity
                        if client_id in self.client_info:
                            self.client_info[client_id]['last_activity'] = time.time()
                        
                        # Broadcast message to appropriate clients
                        await self._broadcast_message(data, client_type, client_id)
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": {
                            "message": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
        finally:
            # Clean up client
            if client_type and client_type in self.clients:
                self.clients[client_type].discard(websocket)
            if client_id in self.client_info:
                del self.client_info[client_id]
            if client_id in self.client_heartbeats:
                del self.client_heartbeats[client_id]
    
    async def _broadcast_message(self, message: Dict[str, Any], source_type: str, source_id: str):
        """Broadcast message to appropriate clients."""
        try:
            # Determine target clients based on message type and source
            target_types = set()
            
            if message.get('type') == 'memory_update':
                target_types.update(['frontend', 'backend'])
            elif message.get('type') == 'llm_response':
                target_types.update(['frontend', 'memory'])
            elif message.get('type') == 'sensor_data':
                target_types.update(['frontend', 'memory', 'llm'])
            else:
                # Default: broadcast to all except source
                target_types = set(self.clients.keys()) - {source_type}
            
            # Send message to target clients
            for client_type in target_types:
                for client in self.clients[client_type]:
                    try:
                        await client.send(json.dumps(message))
                    except websockets.exceptions.ConnectionClosed:
                        self.clients[client_type].discard(client)
                    except Exception as e:
                        logger.error(f"Error sending message to {client_type} client: {e}")
        
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    
    async def _cleanup_stale_connections(self):
        """Periodically clean up stale connections."""
        while self.running:
            try:
                current_time = time.time()
                for client_id, last_heartbeat in list(self.client_heartbeats.items()):
                    if current_time - last_heartbeat > self.heartbeat_timeout:
                        logger.warning(f"Client {client_id} heartbeat timeout")
                        if client_id in self.client_info:
                            client_type = self.client_info[client_id]['type']
                            # Find and remove the client's websocket
                            for client in self.clients[client_type]:
                                if client.id == client_id:
                                    self.clients[client_type].discard(client)
                                    break
                            del self.client_info[client_id]
                        del self.client_heartbeats[client_id]
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(self.cleanup_interval)
    
    async def _broadcast_status(self):
        """Periodically broadcast server status to all clients."""
        while self.running:
            try:
                status = {
                    "type": "status_update",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "clients": {
                            client_type: len(clients)
                            for client_type, clients in self.clients.items()
                        },
                        "message_stats": dict(self.message_stats)
                    }
                }
                
                # Broadcast to all clients
                for client_type in self.clients:
                    for client in self.clients[client_type]:
                        try:
                            await client.send(json.dumps(status))
                        except websockets.exceptions.ConnectionClosed:
                            self.clients[client_type].discard(client)
                        except Exception as e:
                            logger.error(f"Error sending status to {client_type} client: {e}")
                
            except Exception as e:
                logger.error(f"Error broadcasting status: {e}")
            
            await asyncio.sleep(5)  # Update every 5 seconds

async def main():
    """Main function to start the bridge server."""
    server = BridgeServer()
    if await server.start():
        try:
            # Keep the server running
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        finally:
            await server.stop()
    else:
        logger.error("Failed to start server")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
