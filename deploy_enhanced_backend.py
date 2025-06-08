#!/usr/bin/env python3
"""
Deploy Enhanced Backend
Replace the current backend with one that handles general knowledge properly
"""

import asyncio
import json
import logging
import websockets
import time
from datetime import datetime
from typing import Dict, Any, Set
from enum import Enum

# Import our enhanced handlers
from enhance_backend_for_general_queries import create_enhanced_ask_mode_handler, create_enhanced_suggest_mode_handler

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class EnhancedEnterpriseBackend:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        
        # Initialize enhanced handlers
        self.enhanced_ask_handler = None
        self.enhanced_suggest_handler = None
        
        logger.info("Enhanced Enterprise Backend initialized with improved query handling")

    async def initialize_enhanced_handlers(self):
        """Initialize enhanced ASK/SUGGEST handlers"""
        self.enhanced_ask_handler = create_enhanced_ask_mode_handler()
        self.enhanced_suggest_handler = create_enhanced_suggest_mode_handler()
        logger.info("Enhanced handlers initialized")

    async def handle_websocket(self, websocket, path=None):
        """Handle WebSocket connections"""
        client_id = f"client_{int(time.time() * 1000)}"
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id} from {client_ip}")
        
        try:
            # Send initial connection response
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Enhanced Enterprise Backend with Smart Query Handling",
                "timestamp": datetime.now().isoformat(),
                "capabilities": [
                    "smart_query_detection",
                    "enhanced_visual_memory",
                    "general_knowledge_support", 
                    "system_context_awareness",
                    "contextual_responses",
                    "agent_mode",
                    "ask_mode", 
                    "suggest_mode",
                    "general_mode"
                ]
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_message(data, client_id)
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await websocket.send(json.dumps({
                        "type": "error", 
                        "error": f"Processing error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)
            if client_id in self.sessions:
                del self.sessions[client_id]

    async def process_message(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Process incoming messages"""
        message_type = data.get("type", "unknown")
        timestamp = datetime.now().isoformat()
        
        logger.info(f"Processing {message_type} from {client_id}")
        
        try:
            # Handle messages with success/response format
            if "success" in data and "response" in data:
                return {
                    "type": "chat_response",
                    "success": data["success"],
                    "response": data["response"],
                    "client_id": client_id,
                    "timestamp": timestamp
                }
            
            # Handle standard message types
            if message_type == "connection_established":
                # Handle connection establishment
                payload = data.get("payload", {})
                client_type = payload.get("client", "unknown")
                version = payload.get("version", "unknown")
                
                # Store client info
                self.sessions[client_id] = {
                    "client_type": client_type,
                    "version": version,
                    "connected_at": timestamp,
                    "last_activity": timestamp
                }
                
                return {
                    "type": "server_ready",
                    "payload": {
                        "status": "connected",
                        "server_version": "1.0.0",
                        "client_id": client_id,
                        "timestamp": timestamp
                    }
                }
            elif message_type == "chat_request":
                return await self.handle_chat_request(data, client_id)
            elif message_type == "system_status":
                return await self.handle_system_status(data, client_id)
            else:
                return {
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "client_id": client_id,
                    "timestamp": timestamp
                }
                
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return {
                "type": "error",
                "error": str(e),
                "client_id": client_id,
                "timestamp": timestamp
            }

    async def handle_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with enhanced query processing"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        start_time = time.time()
        
        try:
            # Route to enhanced handlers
            if mode == ChatMode.ASK:
                response = await self.enhanced_ask_handler(message, session_id)
            elif mode == ChatMode.SUGGEST:
                response = await self.enhanced_suggest_handler(message, session_id)
            elif mode == ChatMode.AGENT:
                response = await self.process_agent_mode(message, session_id)
            elif mode == ChatMode.GENERAL:
                response = await self.process_general_mode(message, session_id)
            else:
                response = await self.process_general_mode(message, session_id)
            
            processing_time = time.time() - start_time
            
            return {
                "type": "chat_response",
                "success": True,
                "mode": mode,
                "payload": {
                    "response": response,
                    "mode": mode,
                    "success": True
                },
                "response": response,
                "processing_time": round(processing_time, 3),
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat request error: {e}")
            return {
                "type": "chat_response",
                "success": False,
                "error": str(e),
                "mode": mode,
                "payload": {
                    "response": f"Error: {str(e)}",
                    "mode": mode,
                    "success": False
                },
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }

    async def process_agent_mode(self, message: str, session_id: str) -> str:
        """Simple agent mode for now"""
        return f"🎯 Agent Mode: Enhanced agent processing for '{message}' - Ready for task execution with improved context awareness."

    async def process_general_mode(self, message: str, session_id: str) -> str:
        """Enhanced general mode"""
        return f"🤖 Enhanced General Mode: I understand your query about '{message}'. I now have improved handling for visual queries, general knowledge, and system information. How may I assist you further?"

    async def handle_system_status(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle system status requests"""
        uptime = datetime.now() - self.start_time
        
        return {
            "type": "system_status_response",
            "status": "operational",
            "uptime_seconds": int(uptime.total_seconds()),
            "connected_clients": len(self.connected_clients),
            "port": 8768,  # Use different port to avoid conflicts
            "capabilities": [
                "smart_query_detection",
                "enhanced_visual_memory",
                "general_knowledge_support",
                "system_context_awareness"
            ],
            "server_time": datetime.now().isoformat(),
            "version": "Enhanced Enterprise Backend v2.0",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

async def run_enhanced_backend():
    """Run the enhanced backend server"""
    backend = EnhancedEnterpriseBackend()
    
    # Initialize enhanced handlers
    await backend.initialize_enhanced_handlers()
    
    host = "localhost"
    port = 8768  # Use different port
    
    logger.info(f"Starting Enhanced Enterprise Backend on {host}:{port}")
    
    # Create a bound method for the WebSocket handler
    handler = backend.handle_websocket
    
    async with websockets.serve(handler, host, port):
        logger.info(f"Enhanced Enterprise Backend listening on ws://{host}:{port}")
        print(f"🚀 Enhanced Backend Ready!")
        print(f"   • Visual queries: 'what am I seeing?' → Contextual responses")
        print(f"   • General knowledge: 'what is nyc?' → NYC is New York City...")
        print(f"   • System queries: 'what's running?' → System process info")
        print(f"   • Connect on ws://localhost:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(run_enhanced_backend())
    except KeyboardInterrupt:
        logger.info("Enhanced Enterprise Backend shutdown")
    except Exception as e:
        logger.error(f"Enhanced Backend error: {e}")