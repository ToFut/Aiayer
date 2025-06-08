#!/usr/bin/env python3
"""
Enterprise Backend 8767 with Real AI Integration
Provides actual intelligent responses instead of templates
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
from datetime import datetime
from typing import Dict, Any, Set
from enum import Enum

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enterprise_8767_real_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class RealAIBackend:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = self.check_ollama_availability()
        logger.info(f"Real AI Backend initialized - Ollama available: {self.ollama_available}")

    def check_ollama_availability(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            try:
                # Try to start Ollama if it's not running
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                return response.status_code == 200
            except:
                return False

    async def get_real_ai_response(self, prompt: str, mode: str, user_id: str = "default", session_id: str = "default") -> str:
        """Route to brain router system - each mode has specialized backend functionality"""
        try:
            # Import brain router
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'brain'))
            
            from brain.core.brain_router import process_chat_request
            
            # Process through brain router
            result = await process_chat_request(
                mode=mode,
                query=prompt,
                user_id=user_id,
                session_id=session_id,
                context={}
            )
            
            if result["success"]:
                mode_prefix = self.get_mode_prefix(mode)
                return f"{mode_prefix} {result['response']}"
            else:
                mode_prefix = self.get_mode_prefix(mode)
                return f"{mode_prefix} {result['response']}"
                
        except Exception as e:
            logger.error(f"Brain router error: {e}")
            # Fallback to direct Ollama for General mode only
            if mode == ChatMode.GENERAL:
                return await self.get_ollama_response(prompt, mode)
            else:
                mode_prefix = self.get_mode_prefix(mode)
                return f"{mode_prefix} Brain router temporarily unavailable. Please try again."

    async def get_ollama_response(self, prompt: str, mode: str) -> str:
        """Get response from Ollama LLM with improved reliability and retries"""
        max_retries = 3
        timeout_values = [10, 15, 20]  # Progressive timeout increase
        
        for attempt in range(max_retries):
            try:
                # Check if Ollama is available before each attempt
                if not self.ollama_available:
                    logger.info(f"Attempt {attempt + 1}: Checking Ollama availability...")
                    self.ollama_available = self.check_ollama_availability()
                    if not self.ollama_available:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                
                # Enhance prompt based on mode
                system_prompt = self.get_system_prompt_for_mode(mode)
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
                
                # Try different models in order of preference
                models_to_try = ["llama3.2:latest", "llama3.2", "llama3:latest", "llama3"]
                
                for model in models_to_try:
                    try:
                        payload = {
                            "model": model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "max_tokens": 500
                            }
                        }
                        
                        logger.info(f"Attempt {attempt + 1}: Trying Ollama with model {model}, timeout {timeout_values[attempt]}s")
                        
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json=payload,
                            timeout=timeout_values[attempt]
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            ai_response = result.get("response", "").strip()
                            
                            if ai_response:  # Make sure we got a real response
                                # Add mode-specific prefix
                                mode_prefix = self.get_mode_prefix(mode)
                                logger.info(f"✅ Success! Got real AI response from {model}")
                                return f"{mode_prefix} {ai_response}"
                        else:
                            logger.warning(f"Ollama request failed with status {response.status_code}: {response.text}")
                    
                    except requests.exceptions.Timeout:
                        logger.warning(f"Timeout with model {model}, trying next model...")
                        continue
                    except Exception as model_error:
                        logger.warning(f"Error with model {model}: {model_error}")
                        continue
                
                # If all models failed for this attempt, wait before retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"All models failed for attempt {attempt + 1}, waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # If all attempts failed, return an error message indicating real failure
        logger.error("❌ All Ollama attempts failed - No mock responses available")
        mode_prefix = self.get_mode_prefix(mode)
        return f"{mode_prefix} I apologize, but I'm currently unable to connect to the AI system. Please check that Ollama is running with 'ollama serve' and try again. This is a real AI system - no mock responses are provided."


    def get_system_prompt_for_mode(self, mode: str) -> str:
        """Get system prompt for each mode"""
        prompts = {
            ChatMode.AGENT: "You are an AI agent specialized in UI automation and task execution. Provide clear, actionable responses for user interface tasks. Be specific about steps and safety considerations.",
            ChatMode.ASK: "You are an AI assistant specialized in answering questions and retrieving information. Provide accurate, helpful responses based on the user's query. Focus on being informative and precise.",
            ChatMode.SUGGEST: "You are an AI assistant specialized in providing proactive suggestions and optimization advice. Analyze the user's context and provide helpful recommendations for improvement.",
            ChatMode.GENERAL: "You are a helpful AI assistant. Provide clear, conversational responses to user queries. Be friendly, informative, and helpful."
        }
        return prompts.get(mode, prompts[ChatMode.GENERAL])

    def get_mode_prefix(self, mode: str) -> str:
        """Get emoji prefix for each mode"""
        prefixes = {
            ChatMode.AGENT: "🎯",
            ChatMode.ASK: "💭", 
            ChatMode.SUGGEST: "💡",
            ChatMode.GENERAL: "🤖"
        }
        return prefixes.get(mode, "🤖")


    async def handle_websocket(websocket, path=None):
        """Handle WebSocket connections with real AI integration"""
        client_id = f"client_{int(time.time() * 1000)}"
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id} from {client_ip}")
        
        try:
            # Send initial connection response
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Real AI Enterprise Backend 8767",
                "timestamp": datetime.now().isoformat(),
                "ai_features": {
                    "ollama_available": self.ollama_available,
                    "intelligent_fallback": True,
                    "real_responses": True
                },
                "capabilities": [
                    "real_ai_responses",
                    "ollama_integration", 
                    "intelligent_processing",
                    "agent_automation",
                    "knowledge_retrieval",
                    "proactive_suggestions"
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
        """Process incoming messages with real AI"""
        message_type = data.get("type", "unknown")
        timestamp = datetime.now().isoformat()
        
        logger.info(f"Processing {message_type} from {client_id}")
        
        try:
            if message_type == "chat_request":
                return await self.handle_chat_request_with_ai(data, client_id)
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

    async def handle_chat_request_with_ai(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with real AI processing"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        start_time = time.time()
        
        try:
            # Get real AI response using brain router system
            ai_response = await self.get_real_ai_response(message, mode, client_id, session_id)
            
            processing_time = time.time() - start_time
            
            return {
                "type": "chat_response",
                "success": True,
                "mode": mode,
                "payload": {
                    "response": ai_response,
                    "mode": mode,
                    "success": True,
                    "ai_powered": True,
                    "ollama_used": self.ollama_available
                },
                "response": ai_response,
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
                    "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                    "mode": mode,
                    "success": False
                },
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }

    async def handle_system_status(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle system status requests"""
        uptime = datetime.now() - self.start_time
        
        return {
            "type": "system_status_response",
            "status": "operational",
            "uptime_seconds": int(uptime.total_seconds()),
            "connected_clients": len(self.connected_clients),
            "port": 8765,
            "ai_features": {
                "ollama_available": self.ollama_available,
                "real_ai_responses": True,
                "intelligent_fallback": True
            },
            "capabilities": [
                "real_ai_integration",
                "ollama_llm_support", 
                "intelligent_processing",
                "enterprise_automation"
            ],
            "server_time": datetime.now().isoformat(),
            "version": "Real AI Enterprise Backend 8767 v2.0",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Start the Real AI Enterprise Backend on port 8767"""
    backend = RealAIBackend()
    
    # Create logs directory
    import os
    os.makedirs("logs/backend", exist_ok=True)
    
    logger.info("🚀 Starting Real AI Enterprise Backend on port 8765...")
    logger.info("🧠 Real AI responses enabled")
    logger.info("🎯 Modes: Agent, Ask, Suggest, General with AI")
    
    try:
        start_server = websockets.serve(
            backend.handle_websocket,
            "localhost", 
            8765,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("✅ Real AI Enterprise Backend started successfully on port 8765")
        logger.info("🌐 WebSocket server listening on ws://localhost:8765")
        logger.info(f"🤖 Ollama integration: {'✅ Active' if backend.ollama_available else '⚠️ Fallback mode'}")
        
        await start_server
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start Real AI Enterprise Backend 8767: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Real AI Enterprise Backend 8767 stopped by user")
    except Exception as e:
        logger.error(f"❌ Real AI Enterprise Backend 8767 error: {e}")