#!/usr/bin/env python3
"""
Smart Progressive Backend with Real AI Integration
Handles slow llama3.2:latest responses with progressive typing indicators
and stage-by-stage updates to keep users engaged during processing
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
import threading
from datetime import datetime
from typing import Dict, Any, Set, Optional
from enum import Enum

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/smart_progressive_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class ProgressStage(str, Enum):
    RECEIVED = "Message received, initializing..."
    ANALYZING = "🧠 Analyzing your request..."
    PROCESSING = "⚡ Processing with AI model..."
    GENERATING = "✍️ Generating thoughtful response..."
    FINALIZING = "🎯 Finalizing response..."
    COMPLETE = "✅ Response ready!"

class SmartProgressiveBackend:
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = self.check_ollama_availability()
        self.active_requests: Dict[str, bool] = {}  # Track active requests
        logger.info(f"Smart Progressive Backend initialized - Ollama available: {self.ollama_available}")

    def check_ollama_availability(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            logger.info(f"Ollama check response: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            try:
                # Try to start Ollama if it's not running
                logger.info("Attempting to start Ollama...")
                subprocess.run(['ollama', 'serve'], check=False, capture_output=True)
                time.sleep(3)
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                return response.status_code == 200
            except Exception as e2:
                logger.error(f"Failed to start Ollama: {e2}")
                return False

    async def send_progress_update(self, websocket: websockets.WebSocketServerProtocol, 
                                 stage: ProgressStage, session_id: str, mode: str):
        """Send a progress update to the client"""
        try:
            progress_message = {
                "type": "progress_update",
                "stage": stage.value,
                "session_id": session_id,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "is_typing": True
            }
            await websocket.send(json.dumps(progress_message))
            logger.info(f"Sent progress update: {stage.value}")
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    async def get_ollama_response(self, message: str, mode: str, websocket: websockets.WebSocketServerProtocol, 
                                session_id: str) -> str:
        """Get response from Ollama with progressive updates"""
        try:
            # Mark request as active
            self.active_requests[session_id] = True
            
            # Stage 1: Analyzing
            await self.send_progress_update(websocket, ProgressStage.ANALYZING, session_id, mode)
            await asyncio.sleep(1)
            
            # Stage 2: Processing
            await self.send_progress_update(websocket, ProgressStage.PROCESSING, session_id, mode)
            
            # Prepare the prompt based on mode
            system_prompts = {
                ChatMode.AGENT: "You are an intelligent AI assistant capable of performing tasks and taking actions. Provide helpful, actionable responses.",
                ChatMode.ASK: "You are a knowledgeable AI assistant. Provide clear, informative answers to questions.",
                ChatMode.SUGGEST: "You are an optimization expert. Analyze the input and provide practical suggestions for improvement.",
                ChatMode.GENERAL: "You are a friendly, helpful AI assistant. Respond naturally and helpfully to any request."
            }
            
            system_prompt = system_prompts.get(ChatMode(mode), system_prompts[ChatMode.GENERAL])
            
            # Prepare Ollama request with extended timeout
            ollama_payload = {
                "model": "llama3.2:latest",
                "prompt": f"System: {system_prompt}\n\nUser: {message}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }
            
            # Stage 3: Generating
            await self.send_progress_update(websocket, ProgressStage.GENERATING, session_id, mode)
            
            # Make the request with extended timeout (60 seconds instead of 10)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=ollama_payload,
                timeout=60  # Extended timeout for slow responses
            )
            
            if response.status_code == 200:
                # Stage 4: Finalizing
                await self.send_progress_update(websocket, ProgressStage.FINALIZING, session_id, mode)
                await asyncio.sleep(0.5)
                
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                if ai_response:
                    logger.info(f"Successfully got Ollama response for {mode} mode")
                    return ai_response
                else:
                    logger.warning("Empty response from Ollama")
                    return self.get_fallback_response(message, mode)
            else:
                logger.error(f"Ollama HTTP error: {response.status_code}")
                return self.get_fallback_response(message, mode)
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after 60 seconds")
            return self.get_fallback_response(message, mode)
        except Exception as e:
            logger.error(f"Error getting Ollama response: {e}")
            return self.get_fallback_response(message, mode)
        finally:
            # Mark request as complete
            self.active_requests[session_id] = False

    def get_fallback_response(self, message: str, mode: str) -> str:
        """Provide intelligent fallback responses when Ollama is unavailable"""
        fallback_responses = {
            ChatMode.AGENT: f"I understand you want me to help with: '{message}'. While I'm experiencing some technical difficulties connecting to my primary AI engine, I can still assist you. Could you provide more specific details about what you'd like me to do?",
            
            ChatMode.ASK: f"Regarding your question about '{message}', I'm currently experiencing connectivity issues with my main knowledge base. However, I can provide some general guidance: Could you rephrase your question or break it down into more specific parts?",
            
            ChatMode.SUGGEST: f"For optimization suggestions regarding '{message}', I recommend: 1) Analyzing current performance metrics, 2) Identifying bottlenecks or pain points, 3) Researching best practices in this area, 4) Implementing incremental improvements. Would you like me to focus on any specific aspect?",
            
            ChatMode.GENERAL: f"I received your message about '{message}'. While I'm having some technical connectivity issues, I'm still here to help. Could you tell me more about what you're looking for or how I can best assist you?"
        }
        
        return fallback_responses.get(ChatMode(mode), fallback_responses[ChatMode.GENERAL])

    async def process_chat_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Process incoming chat requests with progressive updates"""
        try:
            message = data.get('message', '').strip()
            mode = data.get('mode', 'General')
            session_id = data.get('session_id', f'session_{int(time.time())}')
            
            if not message:
                await self.send_error_response(websocket, "Empty message received")
                return
            
            logger.info(f"Processing {mode} request: '{message[:50]}...' (session: {session_id})")
            
            # Stage 0: Received
            await self.send_progress_update(websocket, ProgressStage.RECEIVED, session_id, mode)
            
            # Store session info
            self.sessions[session_id] = {
                'last_message': message,
                'mode': mode,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get AI response with progress updates
            if self.ollama_available:
                ai_response = await self.get_ollama_response(message, mode, websocket, session_id)
            else:
                await self.send_progress_update(websocket, ProgressStage.ANALYZING, session_id, mode)
                await asyncio.sleep(1)
                ai_response = self.get_fallback_response(message, mode)
            
            # Stage 5: Complete
            await self.send_progress_update(websocket, ProgressStage.COMPLETE, session_id, mode)
            await asyncio.sleep(0.3)
            
            # Send final response
            response = {
                "success": True,
                "response": ai_response,
                "mode": mode,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "source": "ollama" if self.ollama_available else "fallback",
                "is_typing": False,
                "type": "final_response"
            }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Sent final response for {mode} mode (session: {session_id})")
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            await self.send_error_response(websocket, f"Processing error: {str(e)}")

    async def send_error_response(self, websocket: websockets.WebSocketServerProtocol, error_msg: str):
        """Send error response to client"""
        try:
            error_response = {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "is_typing": False,
                "type": "error_response"
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle individual client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.connected_clients.add(websocket)
        logger.info(f"Client connected: {client_id} (path: {path})")
        
        try:
            # Send welcome message
            welcome = {
                "type": "connection_established",
                "message": "Connected to Smart Progressive AI Backend",
                "server_time": datetime.now().isoformat(),
                "ollama_available": self.ollama_available,
                "features": ["progressive_responses", "extended_timeouts", "smart_fallbacks"]
            }
            await websocket.send(json.dumps(welcome))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    if message_type == 'chat_request':
                        await self.process_chat_request(websocket, data)
                    elif message_type == 'ping':
                        await websocket.send(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                    elif message_type == 'status':
                        status = {
                            "type": "status_response",
                            "server_uptime": str(datetime.now() - self.start_time),
                            "connected_clients": len(self.connected_clients),
                            "ollama_available": self.ollama_available,
                            "active_sessions": len(self.sessions)
                        }
                        await websocket.send(json.dumps(status))
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                    await self.send_error_response(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    await self.send_error_response(websocket, f"Message handling error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"Client {client_id} removed from active connections")

    async def start_server(self, port: int = 8765):
        """Start the WebSocket server"""
        try:
            logger.info(f"Starting Smart Progressive Backend on port {port}")
            
            # Create logs directory if it doesn't exist
            import os
            os.makedirs('logs/backend', exist_ok=True)
            
            server = await websockets.serve(
                self.handle_client,
                "localhost",
                port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info(f"✅ Smart Progressive Backend running on ws://localhost:{port}")
            logger.info(f"📊 Ollama integration: {'✅ Active' if self.ollama_available else '❌ Fallback mode'}")
            logger.info("🚀 Features: Progressive responses, Extended timeouts, Smart fallbacks")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

async def main():
    """Main entry point"""
    backend = SmartProgressiveBackend()
    try:
        await backend.start_server(8765)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())