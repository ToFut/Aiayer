#!/usr/bin/env python3
"""
Simple Working Backend for Agent Mode Testing
Provides basic chat functionality to test Agent mode without heavy imports
"""

import asyncio
import json
import logging
import websockets
import time
from datetime import datetime
from typing import Dict, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWorkingBackend:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        
        logger.info("✅ Simple Working Backend initialized")
    
    async def handle_websocket(self, websocket, path):
        client_id = f"client_{len(self.connected_clients)}_{int(time.time())}"
        self.connected_clients.add(client_id)
        
        try:
            # Send connection established message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "server": "Simple Working Backend",
                "capabilities": ["chat_request", "button_action", "agent_confirmation"]
            }))
            
            logger.info(f"✅ Client {client_id} connected")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_message(data, client_id)
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format",
                        "client_id": client_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error", 
                        "error": str(e),
                        "client_id": client_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)
            logger.info(f"🔌 Client {client_id} disconnected")
    
    async def process_message(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Process incoming messages"""
        message_type = data.get("type", "unknown")
        timestamp = datetime.now().isoformat()
        
        logger.info(f"📨 Processing {message_type} from {client_id}")
        
        if message_type == "chat_request":
            return await self.handle_chat_request(data, client_id)
        elif message_type == "button_action":
            return await self.handle_button_action(data, client_id)
        elif message_type == "agent_confirmation":
            return await self.handle_agent_confirmation(data, client_id)
        elif message_type == "system_status":
            return await self.handle_system_status(data, client_id)
        else:
            return {
                "type": "error",
                "error": f"Unknown message type: {message_type}",
                "client_id": client_id,
                "timestamp": timestamp
            }
    
    async def handle_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests for all modes"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        start_time = time.time()
        
        logger.info(f"🤖 {mode} mode request: {message[:50]}...")
        
        if mode.lower() == "agent":
            return await self.handle_agent_mode(message, session_id, client_id)
        elif mode.lower() == "ask":
            return await self.handle_ask_mode(message, session_id, client_id)
        elif mode.lower() == "suggest":
            return await self.handle_suggest_mode(message, session_id, client_id)
        else:
            return await self.handle_general_mode(message, session_id, client_id)
    
    async def handle_agent_mode(self, message: str, session_id: str, client_id: str) -> Dict[str, Any]:
        """Handle Agent mode - create automation plans"""
        
        # Mock automation plan generation
        plan_id = f"plan_{int(time.time())}"
        
        # Create a realistic automation plan based on the message
        plan = self.create_automation_plan(message, plan_id)
        
        response = {
            "type": "chat_response",
            "mode": "Agent",
            "response": plan["response"],
            "interactive": True,
            "buttons": plan["buttons"],
            "plan_id": plan_id,
            "session_id": session_id,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": 2.5,  # Mock fast response time
            "automation_plan_created": True,
            "requires_approval": True
        }
        
        logger.info(f"✅ Agent mode plan created: {plan_id}")
        return response
    
    def create_automation_plan(self, message: str, plan_id: str) -> Dict[str, Any]:
        """Create a realistic automation plan based on the user's request"""
        message_lower = message.lower()
        
        # Detect what the user wants to do
        if "safari" in message_lower and "search" in message_lower:
            # Safari search automation
            if "flights" in message_lower or "flight" in message_lower:
                return {
                    "response": f"🤖 **Agent Mode - Flight Search Automation Plan**\n\n**Task:** {message}\n\n**Automation Plan:**\n1. 🌐 Open Safari browser\n2. 🔍 Navigate to Google Flights (flights.google.com)\n3. ✈️ Enter departure city: Miami\n4. ✈️ Enter destination city: NYC\n5. 📅 Select travel dates\n6. 🔍 Search for available flights\n7. 📊 Display results with prices and airlines\n\n**Estimated Time:** 30-45 seconds\n**Success Probability:** 95%\n\n*Click DO to execute this automation plan*",
                    "buttons": [
                        {"action": "DO", "label": "Execute Plan", "style": "primary"},
                        {"action": "ADJUST", "label": "Modify Plan", "style": "secondary"},
                        {"action": "DISMISS", "label": "Cancel", "style": "danger"}
                    ]
                }
            else:
                search_term = self.extract_search_term(message)
                return {
                    "response": f"🤖 **Agent Mode - Safari Search Automation Plan**\n\n**Task:** {message}\n\n**Automation Plan:**\n1. 🌐 Open Safari browser\n2. 🔍 Navigate to Google search\n3. ⌨️ Type search query: '{search_term}'\n4. ⏎ Press Enter to search\n5. 📊 Display search results\n\n**Estimated Time:** 15-20 seconds\n**Success Probability:** 98%\n\n*Click DO to execute this automation plan*",
                    "buttons": [
                        {"action": "DO", "label": "Execute Plan", "style": "primary"},
                        {"action": "ADJUST", "label": "Modify Plan", "style": "secondary"},
                        {"action": "DISMISS", "label": "Cancel", "style": "danger"}
                    ]
                }
        
        elif "youtube" in message_lower:
            search_term = self.extract_search_term(message)
            return {
                "response": f"🤖 **Agent Mode - YouTube Automation Plan**\n\n**Task:** {message}\n\n**Automation Plan:**\n1. 🌐 Open Safari/Chrome browser\n2. 📺 Navigate to YouTube.com\n3. 🔍 Click on search box\n4. ⌨️ Type search query: '{search_term}'\n5. ⏎ Press Enter to search\n6. 🎥 Display video results\n7. ▶️ Optionally play first result\n\n**Estimated Time:** 25-30 seconds\n**Success Probability:** 96%\n\n*Click DO to execute this automation plan*",
                "buttons": [
                    {"action": "DO", "label": "Execute Plan", "style": "primary"},
                    {"action": "SIMULATE", "label": "Simulate First", "style": "info"},
                    {"action": "ADJUST", "label": "Modify Plan", "style": "secondary"},
                    {"action": "DISMISS", "label": "Cancel", "style": "danger"}
                ]
            }
        
        elif "open" in message_lower and "calculator" in message_lower:
            return {
                "response": f"🤖 **Agent Mode - Calculator App Automation Plan**\n\n**Task:** {message}\n\n**Automation Plan:**\n1. ⌨️ Press Cmd+Space to open Spotlight\n2. 🔍 Type 'Calculator'\n3. ⏎ Press Enter to launch Calculator app\n4. 🧮 Calculator will open and be ready for use\n\n**Estimated Time:** 5-8 seconds\n**Success Probability:** 99%\n\n*Click DO to execute this automation plan*",
                "buttons": [
                    {"action": "DO", "label": "Execute Plan", "style": "primary"},
                    {"action": "DISMISS", "label": "Cancel", "style": "danger"}
                ]
            }
        
        else:
            # Generic automation plan
            return {
                "response": f"🤖 **Agent Mode - Custom Automation Plan**\n\n**Task:** {message}\n\n**Automation Plan:**\n1. 🔍 Analyze the requested task\n2. 🎯 Identify required applications and steps\n3. ⚡ Execute the automation sequence\n4. ✅ Verify successful completion\n\n**Note:** This appears to be a custom request. The automation system will attempt to fulfill your request using intelligent planning.\n\n**Estimated Time:** 20-60 seconds\n**Success Probability:** 85%\n\n*Click DO to execute this automation plan*",
                "buttons": [
                    {"action": "DO", "label": "Execute Plan", "style": "primary"},
                    {"action": "SIMULATE", "label": "Simulate First", "style": "info"},
                    {"action": "ADJUST", "label": "Modify Plan", "style": "secondary"},
                    {"action": "DISMISS", "label": "Cancel", "style": "danger"}
                ]
            }
    
    def extract_search_term(self, message: str) -> str:
        """Extract search term from message"""
        # Simple extraction logic
        words = message.split()
        
        # Remove common action words
        skip_words = {"open", "search", "for", "on", "youtube", "safari", "google", "find", "look", "up"}
        search_words = [word for word in words if word.lower() not in skip_words]
        
        if search_words:
            return " ".join(search_words)
        else:
            return "search query"
    
    async def handle_button_action(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle button actions (DO, DISMISS, ADJUST, SIMULATE)"""
        action = data.get("action", "").upper()
        plan_id = data.get("plan_id")
        
        logger.info(f"🔘 Button action: {action} for plan {plan_id}")
        
        if action == "DO":
            return {
                "type": "automation_result",
                "success": True,
                "action": action,
                "plan_id": plan_id,
                "response": f"🚀 **Automation Execution Started**\n\nPlan ID: {plan_id}\n\n✅ Step 1: Opening application...\n⏳ Step 2: Navigating to target...\n⏳ Step 3: Performing actions...\n\n*Automation is now running. You'll see updates as each step completes.*",
                "status": "executing",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action == "SIMULATE":
            return {
                "type": "simulation_result",
                "success": True,
                "action": action,
                "plan_id": plan_id,
                "response": f"🎭 **Automation Simulation**\n\nPlan ID: {plan_id}\n\n✅ Simulation completed successfully\n📊 All steps validated\n🎯 Estimated success rate: 96%\n⏱️ Estimated execution time: 25 seconds\n\n*The automation plan looks good! Click DO to execute for real.*",
                "status": "simulated",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action == "ADJUST":
            return {
                "type": "adjustment_options",
                "success": True,
                "action": action,
                "plan_id": plan_id,
                "response": f"⚙️ **Plan Adjustment Options**\n\nPlan ID: {plan_id}\n\n**Available Adjustments:**\n• 🐌 Slower execution (add delays)\n• ⚡ Faster execution (reduce delays)\n• 🎯 Change target application\n• 📝 Modify search terms\n• 🔄 Add verification steps\n\n*Describe what you'd like to adjust, or click DO to proceed with the current plan.*",
                "status": "adjustable", 
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action == "DISMISS":
            return {
                "type": "plan_dismissed",
                "success": True,
                "action": action,
                "plan_id": plan_id,
                "response": f"❌ **Automation Plan Cancelled**\n\nPlan ID: {plan_id}\n\n✅ Plan has been safely cancelled\n🔄 No actions were performed\n💡 Feel free to request a new automation plan anytime\n\n*How else can I help you automate your tasks?*",
                "status": "cancelled",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            return {
                "type": "error",
                "error": f"Unknown button action: {action}",
                "plan_id": plan_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_agent_confirmation(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle agent confirmation (same as button_action for compatibility)"""
        return await self.handle_button_action(data, client_id)
    
    async def handle_ask_mode(self, message: str, session_id: str, client_id: str) -> Dict[str, Any]:
        """Handle Ask mode"""
        return {
            "type": "chat_response",
            "mode": "Ask",
            "response": f"🧠 **Ask Mode Response**\n\nRegarding: \"{message}\"\n\nI can help you with information and context about your current situation. This is a simplified backend for testing Agent mode functionality.\n\n💡 **For full Ask mode capabilities:**\n• Visual context analysis\n• Memory-based responses\n• Semantic search integration\n\n*Switch to Agent mode to create automation plans!*",
            "session_id": session_id,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": 0.8
        }
    
    async def handle_suggest_mode(self, message: str, session_id: str, client_id: str) -> Dict[str, Any]:
        """Handle Suggest mode"""
        return {
            "type": "chat_response",
            "mode": "Suggest",
            "response": f"💡 **Suggest Mode Response**\n\nBased on: \"{message}\"\n\n**My suggestions:**\n• Try using Agent mode for automation tasks\n• Use specific commands like 'open Safari and search for flights'\n• Test the button functionality with the DO button\n\n🎯 **Quick automation ideas:**\n• \"Open calculator\"\n• \"Search YouTube for music\"\n• \"Open Safari and search for weather\"\n\n*This is a simplified backend for testing Agent mode!*",
            "session_id": session_id,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": 1.2
        }
    
    async def handle_general_mode(self, message: str, session_id: str, client_id: str) -> Dict[str, Any]:
        """Handle General mode"""
        return {
            "type": "chat_response",
            "mode": "General",
            "response": f"💬 **General Chat**\n\nYou said: \"{message}\"\n\nThis is a simple working backend for testing Agent mode functionality. \n\n🤖 **Try Agent mode** for automation capabilities:\n• \"Open Safari and search for flights from Miami to NYC\"\n• \"Search YouTube for AI tutorials\"\n• \"Open calculator\"\n\n✨ **This backend supports:**\n• All 4 chat modes (Agent, Ask, Suggest, General)\n• Button actions (DO, DISMISS, ADJUST, SIMULATE)\n• Real automation plan generation\n\n*Perfect for testing the Agent mode bug fixes!*",
            "session_id": session_id,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": 0.5
        }
    
    async def handle_system_status(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle system status requests"""
        uptime = datetime.now() - self.start_time
        
        return {
            "type": "system_status_response",
            "status": "operational",
            "uptime": str(uptime),
            "connected_clients": len(self.connected_clients),
            "capabilities": [
                "Agent mode with real automation plans",
                "Ask/Suggest/General modes",
                "Button actions (DO/DISMISS/ADJUST/SIMULATE)",
                "Fast response times",
                "WebSocket real-time communication"
            ],
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Start the Simple Working Backend"""
    backend = SimpleWorkingBackend()
    
    logger.info("🚀 Starting Simple Working Backend on port 8767...")
    logger.info("🎯 Designed for Agent mode testing")
    logger.info("✅ Supports all 4 modes: Agent, Ask, Suggest, General")
    logger.info("🔘 Supports button actions: DO, DISMISS, ADJUST, SIMULATE")
    
    try:
        start_server = websockets.serve(
            backend.handle_websocket,
            "localhost",
            8767,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("✅ Simple Working Backend started successfully")
        logger.info("🌐 WebSocket server listening on ws://localhost:8767")
        logger.info("🤖 Ready to test Agent mode automation!")
        logger.info("")
        logger.info("🧪 Test with these messages:")
        logger.info('   Agent mode: {"type":"chat_request","mode":"Agent","message":"open Safari and search for flights from Miami to NYC"}')
        logger.info('   Button test: {"type":"button_action","action":"DO","plan_id":"test_plan"}')
        logger.info("")
        
        await start_server
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start Simple Working Backend: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Simple Working Backend stopped by user")
    except Exception as e:
        logger.error(f"❌ Simple Working Backend error: {e}")