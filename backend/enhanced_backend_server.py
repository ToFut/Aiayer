#!/usr/bin/env python3
"""
Enhanced Backend Server
Handles API requests and integrates with the memory system for context-aware responses.
"""

import os
import sys
import json
import logging
import asyncio
import websockets
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

# Ensure log directory exists
log_dir = os.path.join('logs', 'backend')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'backend_server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedBackendServer:
    def __init__(self, host: str = 'localhost', port: int = 8767):
        self.host = host
        self.port = port
        self.clients = set()
        self.memory_system = None
        self.llm_service = None
        self.running = False
        
    async def initialize(self):
        """Initialize the backend server and its dependencies."""
        try:
            # Import here to avoid circular imports
            from memory.memory_system import MemorySystem
            from llm.llm_service import LLMService
            
            # Initialize memory system
            self.memory_system = MemorySystem()
            await self.memory_system.initialize()
            logger.info("Memory system initialized")
            
            # Initialize LLM service
            self.llm_service = LLMService()
            await self.llm_service.initialize()
            logger.info("LLM service initialized")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing backend server: {e}")
            return False
            
    async def handle_client(self, websocket, path=None):
        """Handle client connections and messages."""
        try:
            self.clients.add(websocket)
            logger.info(f"New client connected. Total clients: {len(self.clients)}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_message(data)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message[:100]}...")
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Remaining clients: {len(self.clients)}")
            
    async def process_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and generate responses."""
        try:
            message_type = data.get('type', 'unknown')
            payload = data.get('payload', {})
            
            logger.info(f"Processing message type: {message_type}")
            logger.debug(f"Message payload: {payload}")
            
            if message_type == 'query':
                try:
                    # Get context from memory system
                    context = await self.memory_system.get_context_summary(
                        query=payload.get('query'),
                        limit=3
                    )
                    logger.info(f"Retrieved context with {len(context) if context else 0} items")
                    
                    # Generate response using LLM
                    response = await self.llm_service.generate_response(
                        query=payload.get('query'),
                        context=context
                    )
                    logger.info(f"Generated response: {response[:100]}...")
                    
                    return {
                        "type": "response",
                        "payload": {
                            "response": response,
                            "context": context,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return {
                        "type": "error",
                        "payload": {
                            "error": f"Error processing query: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                
            elif message_type == 'context_update':
                try:
                    # Update context in memory system
                    await self.memory_system.add_to_context_memory(payload)
                    logger.info("Context updated successfully")
                    return {
                        "type": "context_updated",
                        "payload": {
                            "success": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                except Exception as e:
                    logger.error(f"Error updating context: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return {
                        "type": "error",
                        "payload": {
                            "error": f"Error updating context: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                
            elif message_type == 'register':
                logger.info("Handled client registration.")
                return {
                    "type": "registration_confirmed",
                    "payload": {
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            elif message_type == 'connection_established':
                logger.info("Handled connection established message.")
                return {
                    "type": "connection_acknowledged",
                    "payload": {
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            elif message_type == 'context_request':
                logger.info("Handled context request.")
                context = await self.memory_system.get_context_summary(query=None, limit=3)
                return {
                    "type": "context_update",
                    "payload": {
                        "context": context,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            elif message_type == 'user_message':
                try:
                    # Store the message in memory
                    await self.memory_system.add_to_context_memory({
                        'role': 'user',
                        'content': payload.get('query'),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Get context from memory system
                    context = await self.memory_system.get_context_summary(
                        query=payload.get('query'),
                        limit=3
                    )
                    logger.info(f"Retrieved context with {len(context) if context else 0} items")
                    
                    # Generate response using LLM
                    response = await self.llm_service.generate_response(
                        query=payload.get('query'),
                        context=context
                    )
                    logger.info(f"Generated response: {response[:100]}...")
                    
                    # Store the response in memory
                    await self.memory_system.add_to_context_memory({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        "type": "response",
                        "payload": {
                            "response": response,
                            "context": context,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing user message: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return {
                        "type": "error",
                        "payload": {
                            "error": f"Error processing message: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {
                    "type": "error",
                    "payload": {
                        "error": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "payload": {
                    "error": f"An error occurred while processing your request: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    async def start(self):
        """Start the backend server."""
        try:
            if not await self.initialize():
                logger.error("Failed to initialize backend server")
                return False
                
            self.running = True
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10,   # Wait 10 seconds for pong response
                close_timeout=10   # Wait 10 seconds for close handshake
            )
            
            logger.info(f"Backend server started on ws://{self.host}:{self.port}")
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting backend server: {e}")
            return False
            
    async def stop(self):
        """Stop the backend server and cleanup resources."""
        try:
            self.running = False
            
            # Cleanup memory system
            if self.memory_system:
                await self.memory_system.cleanup()
                
            # Cleanup LLM service
            if self.llm_service:
                await self.llm_service.cleanup()
                
            logger.info("Backend server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping backend server: {e}")

async def main():
    """Main function to run the backend server."""
    server = EnhancedBackendServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Backend server stopped by user")
    except Exception as e:
        logger.error(f"Error in backend server: {e}")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main()) 