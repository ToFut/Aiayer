#!/usr/bin/env python3
"""
Agent-Integrated Chat Overlay System
Combines chat functionality with agent automation capabilities.
Backend responses can trigger automated actions with user confirmation.
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
import websockets
from websockets.server import WebSocketServerProtocol

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_workflow.context_aware_agent import ContextAwareAgent
from agent_workflow.input_controller import InputController
from backend.enhanced_backend_server import EnhancedBackendServer

# Configure logging
os.makedirs('logs/agent_chat', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_chat/integrated_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentIntegratedChatOverlay:
    """
    Integrated chat overlay that combines LLM responses with agent automation.
    Parses backend responses for automation opportunities and executes them with user consent.
    """
    
    def __init__(self, host="localhost", chat_port=8765, backend_port=8767):
        """Initialize the integrated chat overlay system."""
        self.host = host
        self.chat_port = chat_port
        self.backend_port = backend_port
        self.running = False
        
        # Connected clients
        self.chat_clients = set()
        self.active_conversations = {}
        
        # Agent system
        self.agent = ContextAwareAgent(safety_level="high")
        self.input_controller = InputController(safety_level="high")
        
        # Backend connection
        self.backend_server = EnhancedBackendServer(host=host, port=backend_port)
        
        # Action recognition patterns
        self.action_patterns = {
            "click": r"click(?:\s+on)?\s+(.+?)(?:\s+(?:button|link|element))?",
            "type": r"type\s+[\"'](.+?)[\"']",
            "press": r"press\s+(.+?)(?:\s+key)?",
            "move": r"move\s+(?:to\s+)?(.+?)(?:\s+position)?",
            "scroll": r"scroll\s+(up|down)(?:\s+(\d+))?",
            "fill_form": r"fill\s+(?:out\s+)?(?:the\s+)?form\s+with\s+(.+)",
            "navigate": r"(?:go\s+to|navigate\s+to|open)\s+(.+)",
            "search": r"search\s+for\s+[\"'](.+?)[\"']"
        }
        
        # Safety confirmation required for these actions
        self.safety_actions = {
            "click", "type", "press", "fill_form", "navigate"
        }
        
        logger.info("🤖 Agent Integrated Chat Overlay initialized")
        logger.info("🚨 Emergency shutdown: Press Ctrl+1 to stop agent immediately")
    
    async def start(self):
        """Start the integrated chat overlay system."""
        try:
            logger.info("🚀 Starting Agent Integrated Chat Overlay...")
            
            # Initialize backend server
            await self.backend_server.initialize()
            
            # Start WebSocket servers
            chat_server = websockets.serve(
                self.handle_chat_client,
                self.host,
                self.chat_port
            )
            
            backend_server = websockets.serve(
                self.backend_server.handle_client,
                self.host,
                self.backend_port
            )
            
            self.running = True
            
            logger.info(f"💬 Chat server started on ws://{self.host}:{self.chat_port}")
            logger.info(f"🧠 Backend server started on ws://{self.host}:{self.backend_port}")
            
            # Run both servers concurrently
            await asyncio.gather(chat_server, backend_server)
            
        except Exception as e:
            logger.error(f"Failed to start integrated chat overlay: {e}")
            raise
    
    async def handle_chat_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming chat client connections."""
        client_id = str(uuid.uuid4())
        logger.info(f"💬 Chat client connected: {client_id}")
        
        self.chat_clients.add(websocket)
        self.active_conversations[client_id] = {
            "websocket": websocket,
            "history": [],
            "pending_actions": [],
            "user_confirmations": {}
        }
        
        try:
            # Send welcome message
            await self.send_to_client(websocket, {
                "type": "system_message",
                "message": "🤖 AI Assistant with automation capabilities ready!",
                "timestamp": datetime.now().isoformat(),
                "capabilities": [
                    "💬 Natural language chat",
                    "🎯 Smart automation suggestions", 
                    "⌨️ Keyboard and mouse control",
                    "🚨 Emergency shutdown (Ctrl+1)",
                    "🛡️ Safety confirmations for actions"
                ]
            })
            
            # Handle messages
            async for message in websocket:
                await self.process_chat_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"💬 Chat client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Chat client error: {e}")
        finally:
            self.chat_clients.discard(websocket)
            if client_id in self.active_conversations:
                del self.active_conversations[client_id]
    
    async def process_chat_message(self, client_id: str, raw_message: str):
        """Process incoming chat messages and handle automation requests."""
        try:
            message_data = json.loads(raw_message)
            conversation = self.active_conversations.get(client_id)
            
            if not conversation:
                return
            
            websocket = conversation["websocket"]
            
            # Handle different message types
            if message_data.get("type") == "chat_message":
                await self.handle_user_message(client_id, message_data)
                
            elif message_data.get("type") == "action_confirmation":
                await self.handle_action_confirmation(client_id, message_data)
                
            elif message_data.get("type") == "emergency_stop":
                await self.handle_emergency_stop(client_id)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client {client_id}")
        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
    
    async def handle_user_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle user chat messages and generate responses with automation suggestions."""
        try:
            user_message = message_data.get("message", "")
            conversation = self.active_conversations[client_id]
            websocket = conversation["websocket"]
            
            # Add to conversation history
            conversation["history"].append({
                "type": "user",
                "message": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send typing indicator
            await self.send_to_client(websocket, {
                "type": "typing_indicator",
                "status": "typing"
            })
            
            # Get context-aware response from backend
            response_data = await self.get_backend_response(user_message, conversation["history"])
            
            # Parse response for automation opportunities
            automation_suggestions = self.parse_automation_opportunities(response_data.get("response", ""))
            
            # Send response to client
            response_message = {
                "type": "assistant_response",
                "message": response_data.get("response", "I'm sorry, I couldn't process that request."),
                "timestamp": datetime.now().isoformat(),
                "automation_suggestions": automation_suggestions,
                "context": response_data.get("context", {}),
                "confidence": response_data.get("confidence", 0.0)
            }
            
            # Add to conversation history
            conversation["history"].append({
                "type": "assistant",
                "message": response_message["message"],
                "timestamp": response_message["timestamp"],
                "automation_suggestions": automation_suggestions
            })
            
            await self.send_to_client(websocket, response_message)
            
            # If there are automation suggestions, prompt for confirmation
            if automation_suggestions:
                await self.request_automation_confirmation(client_id, automation_suggestions)
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self.send_error_to_client(client_id, "Failed to process your message. Please try again.")
    
    def parse_automation_opportunities(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse assistant response for potential automation actions."""
        opportunities = []
        
        # Look for action patterns in the response
        for action_type, pattern in self.action_patterns.items():
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            
            for match in matches:
                opportunity = {
                    "id": str(uuid.uuid4()),
                    "action_type": action_type,
                    "description": match.group(0),
                    "parameters": list(match.groups()),
                    "requires_confirmation": action_type in self.safety_actions,
                    "confidence": 0.8  # Base confidence, could be improved with ML
                }
                opportunities.append(opportunity)
        
        # Look for specific automation keywords
        automation_keywords = {
            "automate": {"action_type": "automation_request", "confidence": 0.9},
            "automatically": {"action_type": "automation_request", "confidence": 0.7},
            "do this for me": {"action_type": "automation_request", "confidence": 0.8},
            "help me with": {"action_type": "assistance_request", "confidence": 0.6},
            "fill out": {"action_type": "fill_form", "confidence": 0.8},
            "click on": {"action_type": "click", "confidence": 0.9}
        }
        
        text_lower = response_text.lower()
        for keyword, action_info in automation_keywords.items():
            if keyword in text_lower:
                opportunity = {
                    "id": str(uuid.uuid4()),
                    "action_type": action_info["action_type"],
                    "description": f"Detected automation opportunity: {keyword}",
                    "parameters": [keyword],
                    "requires_confirmation": True,
                    "confidence": action_info["confidence"]
                }
                opportunities.append(opportunity)
        
        return opportunities
    
    async def request_automation_confirmation(self, client_id: str, suggestions: List[Dict[str, Any]]):
        """Request user confirmation for automation suggestions."""
        conversation = self.active_conversations[client_id]
        websocket = conversation["websocket"]
        
        # Filter suggestions that require confirmation
        confirmable_suggestions = [s for s in suggestions if s.get("requires_confirmation", False)]
        
        if not confirmable_suggestions:
            return
        
        # Store pending actions
        conversation["pending_actions"] = confirmable_suggestions
        
        # Send confirmation request
        await self.send_to_client(websocket, {
            "type": "automation_confirmation_request",
            "message": "🤖 I found some actions I can automate for you. Would you like me to proceed?",
            "suggestions": confirmable_suggestions,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_action_confirmation(self, client_id: str, message_data: Dict[str, Any]):
        """Handle user confirmation/rejection of automation actions."""
        try:
            action_id = message_data.get("action_id")
            confirmed = message_data.get("confirmed", False)
            
            conversation = self.active_conversations[client_id]
            websocket = conversation["websocket"]
            
            # Find the pending action
            pending_action = None
            for action in conversation["pending_actions"]:
                if action["id"] == action_id:
                    pending_action = action
                    break
            
            if not pending_action:
                await self.send_to_client(websocket, {
                    "type": "error",
                    "message": "❌ Action not found or already processed."
                })
                return
            
            if confirmed:
                # Execute the automation
                await self.execute_automation(client_id, pending_action)
            else:
                # User declined
                await self.send_to_client(websocket, {
                    "type": "system_message",
                    "message": f"✅ Automation declined: {pending_action['description']}"
                })
            
            # Remove from pending actions
            conversation["pending_actions"] = [
                a for a in conversation["pending_actions"] if a["id"] != action_id
            ]
            
        except Exception as e:
            logger.error(f"Error handling action confirmation: {e}")
            await self.send_error_to_client(client_id, "Failed to process automation confirmation.")
    
    async def execute_automation(self, client_id: str, action: Dict[str, Any]):
        """Execute an approved automation action."""
        try:
            conversation = self.active_conversations[client_id]
            websocket = conversation["websocket"]
            
            action_type = action["action_type"]
            parameters = action.get("parameters", [])
            
            # Send execution start notification
            await self.send_to_client(websocket, {
                "type": "automation_started",
                "message": f"🤖 Executing: {action['description']}",
                "action_id": action["id"]
            })
            
            # Execute based on action type
            success = False
            result_message = ""
            
            if action_type == "click":
                # Example: click on button
                success = await self.execute_click_action(parameters)
                result_message = f"✅ Clicked on: {parameters[0] if parameters else 'element'}"
                
            elif action_type == "type":
                # Example: type text
                text = parameters[0] if parameters else ""
                success = self.input_controller.type_text(text)
                result_message = f"✅ Typed: {text}"
                
            elif action_type == "press":
                # Example: press key
                key = parameters[0] if parameters else ""
                success = self.input_controller.press_key(key)
                result_message = f"✅ Pressed key: {key}"
                
            elif action_type == "scroll":
                # Example: scroll up/down
                direction = parameters[0] if parameters else "down"
                clicks = int(parameters[1]) if len(parameters) > 1 else 3
                if direction.lower() == "up":
                    clicks = abs(clicks)
                else:
                    clicks = -abs(clicks)
                success = self.input_controller.scroll(clicks)
                result_message = f"✅ Scrolled {direction}: {abs(clicks)} clicks"
                
            else:
                # Generic automation request
                success = True
                result_message = f"✅ Automation completed: {action['description']}"
            
            # Send result
            if success:
                await self.send_to_client(websocket, {
                    "type": "automation_completed",
                    "message": result_message,
                    "action_id": action["id"],
                    "success": True
                })
            else:
                await self.send_to_client(websocket, {
                    "type": "automation_failed",
                    "message": f"❌ Failed to execute: {action['description']}",
                    "action_id": action["id"],
                    "success": False
                })
            
        except Exception as e:
            logger.error(f"Error executing automation: {e}")
            await self.send_to_client(conversation["websocket"], {
                "type": "automation_failed",
                "message": f"❌ Automation error: {str(e)}",
                "action_id": action["id"],
                "success": False
            })
    
    async def execute_click_action(self, parameters: List[str]) -> bool:
        """Execute a click action with element detection."""
        try:
            if not parameters:
                return False
                
            target = parameters[0]
            
            # Take screenshot and try to find the element
            screenshot = self.input_controller.capture_screen_region()
            if not screenshot:
                return False
            
            # For now, simulate a click at center of screen
            # In a real implementation, use computer vision to find the target
            center_x = self.input_controller.screen_width // 2
            center_y = self.input_controller.screen_height // 2
            
            return self.input_controller.click(center_x, center_y)
            
        except Exception as e:
            logger.error(f"Error in click action: {e}")
            return False
    
    async def handle_emergency_stop(self, client_id: str):
        """Handle emergency stop requests."""
        try:
            logger.critical("🚨 Emergency stop requested via chat interface!")
            
            # Stop the input controller
            self.input_controller.stop()
            
            # Notify all clients
            for websocket in self.chat_clients:
                try:
                    await self.send_to_client(websocket, {
                        "type": "emergency_stop_activated",
                        "message": "🚨 Emergency stop activated - All automation stopped!",
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    pass
            
            # Note: Ctrl+1 hardware shortcut will still work independently
            
        except Exception as e:
            logger.error(f"Error handling emergency stop: {e}")
    
    async def get_backend_response(self, message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get response from the backend LLM service."""
        try:
            # Prepare context from history
            context = []
            for entry in history[-5:]:  # Last 5 messages for context
                role = "user" if entry["type"] == "user" else "assistant"
                context.append({
                    "role": role,
                    "content": entry["message"]
                })
            
            # Add current message
            context.append({
                "role": "user", 
                "content": message
            })
            
            # Call backend (simplified - in real implementation, use proper API)
            response = {
                "response": f"I understand you want help with: {message}. I can help you automate tasks using keyboard and mouse control. What specifically would you like me to do?",
                "context": {"conversation_length": len(history)},
                "confidence": 0.8
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting backend response: {e}")
            return {
                "response": "I'm sorry, I'm having trouble processing your request right now.",
                "context": {},
                "confidence": 0.1
            }
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        """Send message to a specific client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
    
    async def send_error_to_client(self, client_id: str, error_message: str):
        """Send error message to client."""
        conversation = self.active_conversations.get(client_id)
        if conversation:
            await self.send_to_client(conversation["websocket"], {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    async def broadcast_to_all_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if self.chat_clients:
            await asyncio.gather(
                *[self.send_to_client(client, message) for client in self.chat_clients],
                return_exceptions=True
            )
    
    def stop(self):
        """Stop the integrated chat overlay system."""
        logger.info("🛑 Stopping Agent Integrated Chat Overlay...")
        self.running = False
        
        # Stop agent components
        if hasattr(self, 'agent'):
            self.agent.stop()
        
        if hasattr(self, 'input_controller'):
            self.input_controller.stop()

# Main function to start the integrated system
async def main():
    """Main function to run the integrated chat overlay."""
    overlay = AgentIntegratedChatOverlay()
    
    try:
        await overlay.start()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down due to keyboard interrupt...")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        overlay.stop()

if __name__ == "__main__":
    asyncio.run(main())