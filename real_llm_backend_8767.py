#!/usr/bin/env python3
"""
Real LLM Backend for Port 8767 - Actually calls Ollama with Integrated Brain Router
"""

import asyncio
import json
import logging
import websockets
import time
import requests
import sys
import os
from datetime import datetime
from typing import Dict, Any, Set, Optional
from enum import Enum

# Add paths for brain router imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import brain router components
try:
    from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode, Priority, process_chat_request
    from brain.handlers.agent_mode_handler import handle_agent_mode
    # Import real automation handler
    from real_agent_automation_handler import handle_real_agent_automation
    BRAIN_ROUTER_AVAILABLE = True
    REAL_AUTOMATION_AVAILABLE = True
    print("✅ Brain Router system loaded successfully")
    print("✅ Real Automation Handler loaded successfully")
except ImportError as e:
    print(f"⚠️ Brain Router not available: {e}")
    BRAIN_ROUTER_AVAILABLE = False
    REAL_AUTOMATION_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/real_llm_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class RealLLMBackend8767:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_url = "http://localhost:11434"
        self.model = "llama3.2:1b"  # Fast model
        self.timeout = 20  # Consistent timeout with other components
        
        # Initialize automation systems
        self.brain_router = None
        self.ask_handler = None
        self.real_automation_available = REAL_AUTOMATION_AVAILABLE
        
        if BRAIN_ROUTER_AVAILABLE:
            try:
                # Import Enhanced Ask handler and Suggest handler
                from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
                from brain.handlers.suggest_mode_handler import handle_suggest_mode
                self.ask_handler = handle_enhanced_ask_mode
                self.suggest_handler = handle_suggest_mode
                logger.info("🧠 Enhanced Ask Mode Handler initialized")
                logger.info("🧠 Suggest Mode Handler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced handlers: {e}")
                # Fallback to original ask handler
                try:
                    from brain.handlers.ask_mode_handler import handle_ask_mode
                    self.ask_handler = handle_ask_mode
                    self.suggest_handler = None
                    logger.info("🧠 Fallback Ask Mode Handler initialized")
                except Exception as e2:
                    logger.error(f"Failed to initialize fallback ask handler: {e2}")
                    self.ask_handler = None
                    self.suggest_handler = None
        
        if REAL_AUTOMATION_AVAILABLE:
            logger.info("🤖 Real Automation Handler ready for AGENT mode")
        
        logger.info("Real LLM Backend 8767 initialized with Brain Router integration")

    async def _check_button_action(self, data: Dict[str, Any], session_id: str) -> Optional[Dict[str, Any]]:
        """Check if this is a button action and handle it"""
        try:
            # Check for button action in message data
            if data.get("type") == "button_action":
                action = data.get("action")
                plan_id = data.get("plan_id")
                
                if action and plan_id:
                    from real_agent_automation_handler import real_agent_handler
                    
                    # Handle execute_plan with progress updates
                    if action == "execute_plan":
                        # Send immediate acknowledgment
                        await self._send_progress_update(session_id, 0, "Starting automation...", 0, 3)
                        
                        # Execute with progress updates
                        result = await real_agent_handler.handle_button_action(action, plan_id, session_id)
                        
                        # Send completion message
                        return {
                            "type": "execution_complete",
                            "mode": "Agent", 
                            "response": result["response"],
                            "success": result["success"],
                            "action": action,
                            "plan_id": plan_id,
                            "ai_powered": True,
                            "client_id": data.get("client_id", session_id),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        # Handle other actions normally
                        result = await real_agent_handler.handle_button_action(action, plan_id, session_id)
                        
                        return {
                            "type": "button_action_response",
                            "mode": "Agent",
                            "response": result["response"],
                            "ai_powered": True,
                            "button_action_processed": True,
                            "action": action,
                            "plan_id": plan_id,
                            "success": result["success"],
                            "client_id": data.get("client_id", session_id),
                            "timestamp": datetime.now().isoformat()
                        }
            
            # Check if message content matches button patterns
            message = data.get("message", "").strip().upper()
            if message in ["DO", "DISMISS", "ADJUST"]:
                # Look for recent plan IDs - this is a simplified approach
                # In a real implementation, you'd track plan IDs per session
                action_map = {
                    "DO": "execute_plan",
                    "DISMISS": "cancel_plan", 
                    "ADJUST": "modify_plan"
                }
                
                # For now, return a message asking for clarification
                return {
                    "type": "final_response",
                    "mode": "Agent",
                    "response": f"🤖 I see you want to {message.lower()} an automation plan. Please use the interactive buttons in the previous message, or create a new automation request.",
                    "ai_powered": True,
                    "button_hint": True,
                    "client_id": data.get("client_id", session_id),
                    "timestamp": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking button action: {e}")
            return None
    
    async def _send_progress_update(self, session_id: str, progress: int, current_step: str, step_number: int, total_steps: int):
        """Send progress update to specific client"""
        # For now, store progress in sessions for the websocket handler to send
        logger.info(f"📊 Progress update for {session_id}: {progress}% - {current_step}")
        
        # Store progress for immediate sending when available
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        
        self.sessions[session_id]["last_progress"] = {
            "type": "execution_progress",
            "progress": progress,
            "currentStep": current_step,
            "stepNumber": step_number,
            "totalSteps": total_steps,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_websocket(self, websocket):
        """Handle WebSocket connections on port 8767"""
        client_id = f"client_{int(time.time() * 1000)}"
        try:
            self.connected_clients.add(client_id)
            logger.info(f"Client connected: {client_id} from {websocket.remote_address[0]}")
            
            # Send connection establishment message
            connection_msg = {
                "type": "connection_established",
                "message": "Real LLM Backend 8767 with Enhanced Ask/Suggest Handlers",
                "client_id": client_id,
                "features": {
                    "enhanced_ask_mode": True,
                    "enhanced_suggest_mode": True,
                    "semantic_search": True,
                    "visual_context": True,
                    "streaming_responses": True,
                    "all_chat_modes": ["ask", "agent", "suggest", "general"]
                },
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(connection_msg))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Processing {data.get('type', 'unknown')} from {client_id}")
                    
                    if data.get("type") == "chat_request":
                        response = await self.handle_chat_request(data, client_id)
                        await websocket.send(json.dumps(response))
                    elif data.get("type") == "register":
                        response = await self.handle_register(data, client_id)
                        await websocket.send(json.dumps(response))
                    elif data.get("type") == "button_action":
                        # Handle button actions explicitly
                        button_response = await self._check_button_action(data, client_id)
                        if button_response:
                            # For execute_plan, send progress updates during execution
                            if data.get("action") == "execute_plan":
                                # Send initial progress
                                progress_data = {
                                    "type": "execution_progress",
                                    "progress": 10,
                                    "currentStep": "Starting automation...",
                                    "stepNumber": 1,
                                    "totalSteps": 3,
                                    "timestamp": datetime.now().isoformat()
                                }
                                await websocket.send(json.dumps(progress_data))
                                
                                # Small delay to simulate progress
                                await asyncio.sleep(0.5)
                                
                                # Send mid progress
                                progress_data = {
                                    "type": "execution_progress", 
                                    "progress": 66,
                                    "currentStep": "Executing automation steps...",
                                    "stepNumber": 2,
                                    "totalSteps": 3,
                                    "timestamp": datetime.now().isoformat()
                                }
                                await websocket.send(json.dumps(progress_data))
                                
                                await asyncio.sleep(0.5)
                                
                                # Send final progress before completion
                                progress_data = {
                                    "type": "execution_progress",
                                    "progress": 95,
                                    "currentStep": "Completing automation...",
                                    "stepNumber": 3,
                                    "totalSteps": 3,
                                    "timestamp": datetime.now().isoformat()
                                }
                                await websocket.send(json.dumps(progress_data))
                                
                                await asyncio.sleep(0.5)
                            
                            await websocket.send(json.dumps(button_response))
                        else:
                            # Default response for unknown button actions
                            response = {
                                "type": "button_action_response",
                                "success": False,
                                "error": "Button action not processed",
                                "client_id": client_id,
                                "timestamp": datetime.now().isoformat()
                            }
                            await websocket.send(json.dumps(response))
                    else:
                        # Handle other message types with default response
                        response = {
                            "type": f"{data.get('type', 'unknown')}_response",
                            "success": True,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)
            logger.info(f"Client disconnected: {client_id}")

    async def handle_register(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle client registration"""
        return {
            "type": "registration_success",
            "connection_id": client_id,
            "server_capabilities": ["real_llm_responses", "chat_modes", "contextual_responses"],
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with Brain Router integration for AGENT mode"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        if not message.strip():
            return {
                "type": "final_response",
                "mode": mode,
                "response": f"{self.get_mode_prefix(mode)} Please provide a message to respond to.",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Check if this is a button action for automation
            if self.real_automation_available and REAL_AUTOMATION_AVAILABLE:
                button_action = await self._check_button_action(data, session_id)
                if button_action:
                    return button_action
            
            # Use Real Automation Handler for AGENT mode
            if mode == "Agent" and self.real_automation_available and REAL_AUTOMATION_AVAILABLE:
                logger.info(f"🤖 Routing AGENT mode to Real Automation Handler: {message}")
                
                try:
                    # Use real automation handler
                    automation_result = await handle_real_agent_automation(message, session_id)
                    
                    if automation_result.get("success"):
                        response_data = {
                            "type": "final_response",
                            "mode": mode,
                            "response": automation_result["response"],
                            "ai_powered": True,
                            "real_automation_used": True,
                            "interactive_mode": automation_result.get("interactive_mode", False),
                            "requires_approval": automation_result.get("requires_approval", False),
                            "plan_id": automation_result.get("plan_id"),
                            "processing_time": automation_result["processing_time"],
                            "automation_available": automation_result.get("automation_available", False),
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Add buttons if available
                        if "buttons" in automation_result:
                            response_data["buttons"] = automation_result["buttons"]
                            response_data["interactive"] = automation_result.get("interactive", False)
                        
                        return response_data
                    else:
                        logger.warning(f"Real Automation failed: {automation_result.get('response', 'Unknown error')}")
                        # Fallback to regular LLM
                except Exception as e:
                    logger.error(f"Error with Real Automation Handler: {e}")
                    # Fallback to regular LLM
            
            # Use Brain Router handlers for Ask and Suggest modes
            elif mode == "Ask" and self.ask_handler and BRAIN_ROUTER_AVAILABLE:
                logger.info(f"🧠 Routing {mode} mode request to Enhanced Brain Router: {message}")
                
                # Create chat request object
                from brain.core.brain_router import ChatRequest, ChatMode, Priority
                request = ChatRequest(
                    mode=ChatMode.ASK,
                    query=message,
                    user_id=client_id,
                    session_id=session_id,
                    timestamp=time.time(),
                    context={"source": "real_llm_backend_8767"}
                )
                
                try:
                    brain_response = await self.ask_handler(request)
                    
                    if brain_response.success:
                        response_data = {
                            "type": "final_response",
                            "mode": mode,
                            "response": brain_response.response,
                            "ai_powered": True,
                            "brain_router_used": True,
                            "enhanced_memory_used": brain_response.metadata.get("enhanced_memory_used", False),
                            "semantic_search_used": brain_response.metadata.get("semantic_search_used", False),
                            "processing_time": brain_response.processing_time,
                            "confidence": brain_response.confidence,
                            "verification_status": brain_response.verification_status,
                            "resources_used": brain_response.resources_used,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Add metadata if available
                        if brain_response.metadata:
                            response_data["metadata"] = brain_response.metadata
                        
                        return response_data
                    else:
                        # Fallback to regular LLM if handler fails
                        logger.warning(f"{mode} Handler failed, falling back to LLM: {brain_response.response}")
                except Exception as e:
                    logger.error(f"Error with {mode} Handler: {e}")
                    # Fallback to regular LLM
            
            elif mode == "Suggest" and hasattr(self, 'suggest_handler') and self.suggest_handler and BRAIN_ROUTER_AVAILABLE:
                logger.info(f"🧠 Routing {mode} mode request to Suggest Handler: {message}")
                
                # Create chat request object for Suggest mode
                from brain.core.brain_router import ChatRequest, ChatMode, Priority
                request = ChatRequest(
                    mode=ChatMode.SUGGEST,
                    query=message,
                    user_id=client_id,
                    session_id=session_id,
                    timestamp=time.time(),
                    context={"source": "real_llm_backend_8767"}
                )
                
                try:
                    brain_response = await self.suggest_handler(request)
                    
                    if brain_response.success:
                        response_data = {
                            "type": "final_response",
                            "mode": mode,
                            "response": brain_response.response,
                            "ai_powered": True,
                            "brain_router_used": True,
                            "suggest_mode_used": brain_response.metadata.get("suggest_mode_used", False),
                            "memory_integrated": brain_response.metadata.get("memory_integrated", False),
                            "processing_time": brain_response.processing_time,
                            "confidence": brain_response.confidence,
                            "verification_status": brain_response.verification_status,
                            "resources_used": brain_response.resources_used,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Add metadata if available
                        if brain_response.metadata:
                            response_data["metadata"] = brain_response.metadata
                        
                        return response_data
                    else:
                        # Fallback to regular LLM if handler fails
                        logger.warning(f"{mode} Handler failed, falling back to LLM: {brain_response.response}")
                except Exception as e:
                    logger.error(f"Error with {mode} Handler: {e}")
                    # Fallback to regular LLM
            
            # Use regular LLM for non-Agent modes or fallback
            llm_response = await self.call_ollama(message, mode)
            
            # Format response with mode prefix
            formatted_response = f"{self.get_mode_prefix(mode)} {llm_response}"
            
            return {
                "type": "final_response",
                "mode": mode,
                "response": formatted_response,
                "ai_powered": True,
                "model_used": self.model,
                "brain_router_used": False,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat request: {e}")
            return {
                "type": "final_response",
                "mode": mode,
                "response": f"{self.get_mode_prefix(mode)} I apologize, but I'm having trouble processing your request right now. Error: {str(e)}",
                "error": str(e),
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }

    async def call_ollama(self, message: str, mode: str) -> str:
        """Make actual API call to Ollama"""
        try:
            # Create mode-specific system prompt
            system_prompt = self.get_system_prompt(mode)
            
            # Prepare the request
            payload = {
                "model": self.model,
                "prompt": f"System: {system_prompt}\n\nUser: {message}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            # Make the request (synchronous in async function)
            import asyncio
            import functools
            
            def make_request():
                try:
                    response = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload,
                        timeout=self.timeout  # Use consistent timeout attribute
                    )
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.ReadTimeout:
                    logger.error("Ollama request timed out - likely processing a large request")
                    raise Exception("Request timed out. The model is taking too long to respond.")
                except requests.exceptions.ConnectionError:
                    logger.error("Ollama connection error - service may be down")
                    raise Exception("Unable to connect to LLM service. Please check if Ollama is running.")
                except Exception as e:
                    logger.error(f"Unexpected Ollama error: {str(e)}")
                    raise
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            for attempt in range(3):  # Try up to 3 times
                try:
                    result = await loop.run_in_executor(None, make_request)
                    return result.get("response", "I don't have a response for that.").strip()
                except Exception as e:
                    if attempt < 2:  # If not last attempt
                        logger.warning(f"Retrying Ollama request ({attempt+1}/3): {str(e)}")
                        await asyncio.sleep(0.5 * (attempt + 1))  # Backoff
                    else:
                        raise  # Last attempt failed, propagate error
            
            # This shouldn't be reached due to the exception above
            return "Error generating response."
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"LLM service unavailable: {str(e)}")

    def get_mode_prefix(self, mode: str) -> str:
        """Get the prefix for each mode"""
        prefixes = {
            "Agent": "🤖 Agent Mode:",
            "Ask": "💭 Ask Mode:",
            "Suggest": "✨ Suggest Mode:",
            "General": "🧠 AI Assistant:"
        }
        return prefixes.get(mode, "🧠 AI Assistant:")

    def get_system_prompt(self, mode: str) -> str:
        """Get system prompt for each mode"""
        prompts = {
            "Agent": "You are an AI agent specialized in helping with tasks and automation. You can help with simple tasks like opening applications, creating documents, and providing actionable guidance. Be direct, helpful, and ready to assist with practical requests. Never refuse reasonable automation tasks.",
            "Ask": "You are an AI assistant specialized in answering questions with depth and accuracy. Provide comprehensive, informative answers.",
            "Suggest": "You are an AI assistant specialized in providing helpful suggestions and recommendations. Offer practical, actionable advice.",
            "General": "You are a helpful AI assistant. Respond naturally and helpfully to the user's message."
        }
        return prompts.get(mode, prompts["General"])

async def main():
    backend = RealLLMBackend8767()
    
    # Start WebSocket server on port 8767
    logger.info("Starting Real LLM Backend on port 8767...")
    
    async with websockets.serve(backend.handle_websocket, "localhost", 8767):
        logger.info("✅ Real LLM Backend is running on ws://localhost:8767")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
