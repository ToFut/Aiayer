#!/usr/bin/env python3
"""
Memory Dashboard Server
Provides a web interface for viewing and managing the memory system.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import websockets
from typing import Dict, Any, Optional

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_dashboard')

class MemoryDashboardServer:
    """Server for the memory dashboard."""
    
    def __init__(self, host="0.0.0.0", port=8082, memory_system_uri="ws://localhost:8765"):
        """Initialize the memory dashboard server."""
        self.host = host
        self.port = port
        self.memory_system_uri = memory_system_uri
        self.running = True
        self.clients = set()
        self.memory_system = None
        
        logger.info("Memory dashboard server initialized")
    
    async def start(self):
        """Start the memory dashboard server."""
        try:
            # Start WebSocket server
            server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            logger.info(f"Memory dashboard server started on ws://{self.host}:{self.port}")
            
            # Connect to memory system
            await self._connect_to_memory_system()
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting memory dashboard server: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _connect_to_memory_system(self):
        """Connect to the memory system."""
        while self.running:
            try:
                async with websockets.connect(self.memory_system_uri) as websocket:
                    self.memory_system = websocket
                    logger.info("Connected to memory system")
                    
                    while self.running:
                        try:
                            # Receive memory state updates
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Broadcast to all connected clients
                            if self.clients:
                                await self._broadcast(data)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Connection to memory system closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in memory system communication: {e}")
                            logger.error(traceback.format_exc())
                            break
                    
            except Exception as e:
                logger.error(f"Error connecting to memory system: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def _handle_client(self, websocket):
        """Handle a new client connection."""
        try:
            # Add client to set
            self.clients.add(websocket)
            logger.info(f"New client connected. Total clients: {len(self.clients)}")
            
            # Send initial memory state if available
            if self.memory_system:
                try:
                    # Request current state from memory system
                    await self.memory_system.send(json.dumps({"type": "get_state"}))
                except Exception as e:
                    logger.error(f"Error requesting initial state: {e}")
                    logger.error(traceback.format_exc())
            
            # Handle client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle client requests
                    if data.get("type") == "get_state":
                        if self.memory_system:
                            await self.memory_system.send(json.dumps({"type": "get_state"}))
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON from client")
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    logger.error(traceback.format_exc())
            
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Remove client from set
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def _broadcast(self, data):
        """Broadcast data to all connected clients."""
        if not self.clients:
            return
        
        # Prepare message
        message = json.dumps(data)
        
        # Send to all clients
        for client in self.clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                self.clients.remove(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                logger.error(traceback.format_exc())
                self.clients.remove(client)
    
    async def stop(self):
        """Stop the memory dashboard server."""
        self.running = False
        if self.memory_system:
            await self.memory_system.close()
        logger.info("Memory dashboard server stopped")

async def main():
    """Main function to run the memory dashboard server."""
    try:
        # Create and start server
        server = MemoryDashboardServer()
        await server.start()
        
    except KeyboardInterrupt:
        logger.info("Memory dashboard server stopped by user")
    except Exception as e:
        logger.error(f"Error in memory dashboard server: {e}")
        logger.error(traceback.format_exc())
    finally:
        if 'server' in locals():
            await server.stop()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())