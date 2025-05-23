#!/usr/bin/env python3
"""
Simple Brain Router WebSocket Server
Fixes common startup issues with a streamlined approach
"""

import asyncio
import json
import logging
import websockets
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask"
    SUGGEST = "Suggest"
    GENERAL = "General"

class SimpleBrainRouter:
    def __init__(self):
        self.sessions = {}
        self.connected_clients = set()
        self.start_time = datetime.now()
        logger.info("Simple Brain Router initialized")

    async def process_request(self, mode: ChatMode, message: str, session_id: str) -> Dict[str, Any]:
        """Process request based on mode"""
        start_time = time.time()
        
        try:
            if mode == ChatMode.AGENT:
                response = await self._handle_agent_mode(message)
            elif mode == ChatMode.ASK:
                response = await self._handle_ask_mode(message)
            elif mode == ChatMode.SUGGEST:
                response = await self._handle_suggest_mode(message)
            elif mode == ChatMode.GENERAL:
                response = await self._handle_general_mode(message)
            else:
                response = await self._handle_general_mode(message)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "response": response,
                "mode": mode.value,
                "processing_time": round(processing_time, 2),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing {mode} request: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": mode.value,
                "session_id": session_id
            }

    async def _handle_agent_mode(self, message: str) -> str:
        """Handle Agent mode - UI automation and task execution"""
        logger.info(f"Agent mode: {message}")
        
        # Simulate agent processing
        await asyncio.sleep(0.1)
        
        if "click" in message.lower():
            return f"🎯 Agent Mode: Executing click operation - {message}"
        elif "open" in message.lower():
            return f"🎯 Agent Mode: Opening application/file - {message}"
        elif "type" in message.lower():
            return f"🎯 Agent Mode: Typing text - {message}"
        else:
            return f"🎯 Agent Mode: Task execution planned for: {message}"

    async def _handle_ask_mode(self, message: str) -> str:
        """Handle Ask mode - Memory queries and knowledge retrieval"""
        logger.info(f"Ask mode: {message}")
        
        # Simulate memory search
        await asyncio.sleep(0.1)
        
        if "status" in message.lower():
            return "💭 Ask Mode: System is running normally. All components active."
        elif "file" in message.lower():
            return "💭 Ask Mode: Recent files include documents, images, and code files."
        elif "memory" in message.lower():
            return "💭 Ask Mode: Memory system is operational with semantic search enabled."
        else:
            return f"💭 Ask Mode: Query processed - {message}"

    async def _handle_suggest_mode(self, message: str) -> str:
        """Handle Suggest mode - Proactive suggestions"""
        logger.info(f"Suggest mode: {message}")
        
        # Simulate suggestion generation
        await asyncio.sleep(0.1)
        
        suggestions = [
            "💡 Suggestion: Optimize your workflow by organizing files",
            "💡 Suggestion: Consider using keyboard shortcuts for efficiency",
            "💡 Suggestion: Regular system maintenance recommended",
            "💡 Suggestion: Update your development environment"
        ]
        
        return f"💡 Suggest Mode: {suggestions[0]} | Context: {message}"

    async def _handle_general_mode(self, message: str) -> str:
        """Handle General mode - Basic conversations"""
        logger.info(f"General mode: {message}")
        
        # Simulate LLM response
        await asyncio.sleep(0.1)
        
        return f"🤖 General Mode: I understand you're asking about '{message}'. How can I help you further?"

    async def handle_websocket(self, websocket):
        """Handle WebSocket connections"""
        client_id = f"client_{int(time.time() * 1000)}"
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Simple Brain Router",
                "available_modes": ["Agent", "Ask", "Suggest", "General"]
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get("type") == "chat_request":
                        mode = ChatMode(data.get("mode", "General"))
                        user_message = data.get("message", "")
                        session_id = data.get("session_id", client_id)
                        
                        result = await self.process_request(mode, user_message, session_id)
                        await websocket.send(json.dumps(result))
                        
                    elif data.get("type") == "system_status":
                        status = self.get_system_status()
                        await websocket.send(json.dumps(status))
                        
                    else:
                        await websocket.send(json.dumps({
                            "error": "Unknown message type",
                            "received": data
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "error": f"Processing error: {str(e)}"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            self.connected_clients.discard(client_id)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime = datetime.now() - self.start_time
        
        return {
            "status": "online",
            "uptime_seconds": int(uptime.total_seconds()),
            "connected_clients": len(self.connected_clients),
            "available_modes": [mode.value for mode in ChatMode],
            "server_time": datetime.now().isoformat(),
            "version": "Simple Brain Router v1.0"
        }

async def main():
    """Start the Simple Brain Router server"""
    brain_router = SimpleBrainRouter()
    
    logger.info("🧠 Starting Simple Brain Router WebSocket Server...")
    logger.info("📡 Port: 8765")
    logger.info("🎯 Modes: Agent, Ask, Suggest, General")
    
    try:
        start_server = websockets.serve(
            brain_router.handle_websocket,
            "localhost",
            8765,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("✅ Simple Brain Router started on ws://localhost:8765")
        
        await start_server
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")