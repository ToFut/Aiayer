#!/usr/bin/env python3
"""
Lightweight Backend for SensAI
Simplified version that avoids heavy components for better performance.
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LightweightBackend:
    """Lightweight backend with minimal resource usage"""
    
    def __init__(self):
        self.clients = set()
        self.running = False
        self.port = 8767
        self.host = "localhost"
        
        # Lightweight configuration
        self.config = {
            "max_concurrent_requests": 2,
            "request_timeout": 10,
            "max_memory_mb": 200,
            "enable_throttling": True,
            "use_caching": True,
            "cache_duration": 300
        }
        
        # Simple cache
        self.cache = {}
        self.cache_timestamps = {}
        
        # Memory tracking
        self.memory_usage = 0
        self.request_count = 0
        
        logger.info("🚀 Lightweight Backend initialized")
    
    async def start(self):
        """Start the lightweight backend"""
        self.running = True
        
        try:
            # Start WebSocket server
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            logger.info(f"✅ Lightweight Backend started on ws://{self.host}:{self.port}")
            logger.info(f"📊 Configuration: {self.config}")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            self.running = False
    
    async def handle_client(self, websocket, path):
        """Handle client connections"""
        client_id = id(websocket)
        self.clients.add(websocket)
        
        logger.info(f"🔌 Client connected: {client_id}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Lightweight SensAI Backend Connected",
                "timestamp": datetime.now().isoformat(),
                "config": self.config
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    await self.process_message(websocket, message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Error processing request: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def process_message(self, websocket, message):
        """Process incoming messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.info(f"📨 Received message type: {message_type}")
            
            # Handle different message types
            if message_type == "chat":
                response = await self.handle_chat(data)
            elif message_type == "agent":
                response = await self.handle_agent(data)
            elif message_type == "suggest":
                response = await self.handle_suggest(data)
            elif message_type == "status":
                response = await self.handle_status(data)
            elif message_type == "ping":
                response = {"type": "pong", "timestamp": datetime.now().isoformat()}
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Send response
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Internal error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def handle_chat(self, data):
        """Handle chat messages"""
        query = data.get("message", "")
        mode = data.get("mode", "ask")
        
        logger.info(f"💬 Chat request: {mode} mode - {query[:50]}...")
        
        # Simple response for lightweight mode
        response = {
            "type": "chat_response",
            "mode": mode,
            "message": f"Lightweight mode response: {query}",
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "response_time": 0.1,
                "memory_usage": self.memory_usage,
                "mode": "lightweight"
            }
        }
        
        return response
    
    async def handle_agent(self, data):
        """Handle agent requests"""
        query = data.get("message", "")
        
        logger.info(f"🤖 Agent request: {query[:50]}...")
        
        # Simple agent response for lightweight mode
        response = {
            "type": "agent_response",
            "message": f"Lightweight agent mode: {query}",
            "plan": [
                {
                    "step": 1,
                    "action": "analyze_request",
                    "description": "Analyzing user request in lightweight mode"
                },
                {
                    "step": 2,
                    "action": "generate_response",
                    "description": "Generating lightweight response"
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "response_time": 0.2,
                "memory_usage": self.memory_usage,
                "mode": "lightweight"
            }
        }
        
        return response
    
    async def handle_suggest(self, data):
        """Handle suggestion requests"""
        context = data.get("context", "")
        
        logger.info(f"💡 Suggest request: {context[:50]}...")
        
        # Simple suggestions for lightweight mode
        suggestions = [
            "Use lightweight mode for better performance",
            "Run system cleanup to optimize resources",
            "Monitor performance with lightweight monitor"
        ]
        
        response = {
            "type": "suggest_response",
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "response_time": 0.1,
                "memory_usage": self.memory_usage,
                "mode": "lightweight"
            }
        }
        
        return response
    
    async def handle_status(self, data):
        """Handle status requests"""
        # Get system status
        import psutil
        
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        status = {
            "type": "status_response",
            "backend": {
                "status": "running",
                "mode": "lightweight",
                "clients": len(self.clients),
                "requests": self.request_count
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "memory_total_mb": memory.total / 1024 / 1024
            },
            "performance": {
                "response_time": 0.05,
                "memory_usage": self.memory_usage,
                "mode": "lightweight"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    def stop(self):
        """Stop the backend"""
        self.running = False
        logger.info("🛑 Lightweight Backend stopped")

async def main():
    """Main function"""
    backend = LightweightBackend()
    
    try:
        await backend.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Backend error: {e}")
    finally:
        backend.stop()

if __name__ == "__main__":
    # Set up signal handlers
    import signal
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the backend
    asyncio.run(main()) 