#!/usr/bin/env python3
"""
Working streaming backend - minimal version for testing
"""

import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingBackend:
    def __init__(self):
        self.connected_clients = set()
        
    async def handle_websocket(websocket, path=None):
        """Handle WebSocket connections"""
        client_id = f"client_{int(datetime.now().timestamp() * 1000)}"
        self.connected_clients.add(client_id)
        
        try:
            # Send connection established
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Working Streaming Backend",
                "timestamp": datetime.now().isoformat(),
                "ai_features": {"ollama_available": True}
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "chat_request":
                        await self.handle_chat_request(data, client_id, websocket)
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.discard(client_id)
    
    async def handle_chat_request(self, data, client_id, websocket):
        """Handle streaming chat requests"""
        mode = data.get("mode", "ask")
        message = data.get("message", "")
        
        logger.info(f"Chat request from {client_id}: {mode} - {message}")
        
        try:
            # Send start message
            await websocket.send(json.dumps({
                "type": "chat_response_start",
                "mode": mode,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "🤖 Processing your request..."
            }))
            
            # Get mode-specific prompt
            system_prompt = self.get_system_prompt(mode)
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
            # Stream from Ollama
            payload = {
                "model": "llama3.2:1b",
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 600
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        full_response = ""
                        chunk_buffer = ""
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if line_text:
                                        chunk_data = json.loads(line_text)
                                        
                                        # Handle response chunk
                                        if chunk_data.get("response"):
                                            chunk_text = chunk_data.get("response", "")
                                            full_response += chunk_text
                                            chunk_buffer += chunk_text
                                            
                                            # Send chunks when buffer is large enough
                                            if len(chunk_buffer) >= 5 or chunk_text.endswith(' '):
                                                await websocket.send(json.dumps({
                                                    "type": "chat_response_chunk",
                                                    "mode": mode,
                                                    "chunk": chunk_buffer,
                                                    "client_id": client_id,
                                                    "timestamp": datetime.now().isoformat()
                                                }))
                                                chunk_buffer = ""
                                        
                                        # Check if done
                                        if chunk_data.get("done", False):
                                            # Send any remaining buffer
                                            if chunk_buffer:
                                                await websocket.send(json.dumps({
                                                    "type": "chat_response_chunk",
                                                    "mode": mode,
                                                    "chunk": chunk_buffer,
                                                    "client_id": client_id,
                                                    "timestamp": datetime.now().isoformat()
                                                }))
                                            
                                            # Send completion
                                            mode_prefix = self.get_mode_prefix(mode)
                                            final_response = f"{mode_prefix} {full_response.strip()}"
                                            
                                            await websocket.send(json.dumps({
                                                "type": "chat_response_complete",
                                                "mode": mode,
                                                "full_response": final_response,
                                                "client_id": client_id,
                                                "timestamp": datetime.now().isoformat(),
                                                "ai_powered": True
                                            }))
                                            
                                            logger.info(f"Response completed for {client_id}: {len(full_response)} chars")
                                            return
                                            
                                except json.JSONDecodeError:
                                    continue
                    else:
                        # Send error
                        await websocket.send(json.dumps({
                            "type": "chat_response_error",
                            "mode": mode,
                            "error": f"Ollama request failed: {response.status}",
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
        except Exception as e:
            logger.error(f"Chat request error: {e}")
            await websocket.send(json.dumps({
                "type": "chat_response_error",
                "mode": mode,
                "error": str(e),
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
    
    def get_system_prompt(self, mode):
        """Get system prompt for each mode"""
        prompts = {
            "ask": "You are a helpful AI assistant that answers questions clearly and accurately.",
            "agent": "You are an AI agent that provides step-by-step guidance and actionable instructions.",
            "suggest": "You are an AI assistant that provides helpful suggestions and recommendations.",
            "general": "You are a friendly AI assistant engaged in natural conversation."
        }
        return prompts.get(mode, prompts["general"])
    
    def get_mode_prefix(self, mode):
        """Get prefix for each mode"""
        prefixes = {
            "ask": "📝",
            "agent": "🤖",
            "suggest": "💡",
            "general": "💬"
        }
        return prefixes.get(mode, "💬")

async def main():
    backend = StreamingBackend()
    
    logger.info("🚀 Starting Working Streaming Backend on port 8767...")
    
    async with websockets.serve(backend.handle_websocket, "localhost", 8767):
        logger.info("✅ Server started on ws://localhost:8767")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())