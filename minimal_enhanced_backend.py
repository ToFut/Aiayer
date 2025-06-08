#!/usr/bin/env python3
"""
Minimal Enhanced Enterprise Backend 8767
Provides basic AI responses with fallback to simple backend
"""

import asyncio
import json
import logging
import websockets
import time
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Set, Optional
from enum import Enum

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/minimal_enhanced_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class MinimalEnhancedBackend:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = False
        logger.info("✅ Minimal enhanced backend initialized")
        
    async def handle_websocket(self, websocket, path=None):
        client_id = str(uuid.uuid4())
        self.connected_clients.add(client_id)
        self.sessions[client_id] = {
            "start_time": datetime.now(),
            "last_active": datetime.now(),
            "mode": ChatMode.GENERAL
        }
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.handle_message(data, client_id, websocket)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Internal server error: {str(e)}"
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.connected_clients.remove(client_id)
            if client_id in self.sessions:
                del self.sessions[client_id]
    
    async def handle_message(self, data: Dict[str, Any], client_id: str, websocket) -> Dict[str, Any]:
        if "type" not in data:
            return {
                "type": "error",
                "message": "Missing message type"
            }
            
        if data["type"] == "chat":
            return await self.handle_chat_request(data, client_id, websocket)
        elif data["type"] == "agent":
            return await self.handle_agent_request(data, client_id, websocket)
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {data['type']}"
            }
    
    async def handle_chat_request(self, data: Dict[str, Any], client_id: str, websocket) -> Dict[str, Any]:
        if "message" not in data:
            return {
                "type": "error",
                "message": "Missing message content"
            }
            
        # For now, just echo the message back
        return {
            "type": "response",
            "message": f"Echo: {data['message']}",
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_agent_request(self, data: Dict[str, Any], client_id: str, websocket) -> Dict[str, Any]:
        if "message" not in data:
            return {
                "type": "error",
                "message": "Missing message content"
            }
            
        # For now, just echo the message back with agent prefix
        return {
            "type": "response",
            "message": f"Agent Echo: {data['message']}",
            "timestamp": datetime.now().isoformat()
        }

async def start_server():
    server = await websockets.serve(
        MinimalEnhancedBackend().handle_websocket,
        "localhost",
        8767
    )
    logger.info("🚀 Minimal enhanced backend server started on port 8767")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 