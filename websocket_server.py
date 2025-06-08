from typing import Dict, Any
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('websocket_server')

class WebSocketServer:
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            if not message_type:
                logger.warning("⚠️ Received message without type")
                return
            
            # Handle different message types
            if message_type == "button_action":
                await self._handle_button_action(message)
            elif message_type == "agent_confirmation":
                await self._handle_agent_confirmation(message)
            elif message_type == "overlay_session":
                await self._handle_overlay_session(message)
            elif message_type == "chat_request":
                await self._handle_chat_request(message)
            elif message_type == "chat_response":
                await self._handle_chat_response(message)
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            await self.send_error_response(str(e))

    async def _handle_button_action(self, message: Dict[str, Any]) -> None:
        """Handle button action messages"""
        try:
            # Extract required fields
            action = message.get("action")
            plan_id = message.get("plan_id")
            session_id = message.get("session_id")
            
            if not all([action, plan_id, session_id]):
                logger.warning("⚠️ Missing required fields in button action")
                await self.send_error_response("Missing required fields")
                return
            
            # Get universal automation handler
            from universal_intelligent_automation_handler import universal_automation_handler
            
            # Handle the button action
            result = await universal_automation_handler.handle_button_action(
                action=action,
                plan_id=plan_id,
                session_id=session_id
            )
            
            # Send response
            await self.send_response({
                "type": "button_action_response",
                "success": result["success"],
                "plan_id": plan_id,
                "status": result.get("status", "unknown"),
                "message": result.get("message", ""),
                "execution_time": result.get("execution_time", 0),
                "success_rate": result.get("success_rate", 0)
            })
            
        except Exception as e:
            logger.error(f"❌ Error handling button action: {e}")
            await self.send_error_response(str(e))

    async def _handle_agent_confirmation(self, message: Dict[str, Any]) -> None:
        """Handle agent confirmation messages"""
        try:
            # Extract required fields
            session_id = message.get("session_id")
            if not session_id:
                logger.warning("⚠️ Missing session_id in agent confirmation")
                await self.send_error_response("Missing session_id")
                return
            
            # Convert agent confirmation to button action
            button_action = {
                "type": "button_action",
                "action": "DO",
                "session_id": session_id
            }
            
            # Try to find the plan ID
            if "plan_id" in message:
                button_action["plan_id"] = message["plan_id"]
            else:
                # Try to find the newest plan
                from universal_intelligent_automation_handler import universal_automation_handler
                newest_plan = await universal_automation_handler._find_newest_plan()
                if newest_plan:
                    button_action["plan_id"] = newest_plan.plan_id
                else:
                    logger.warning("⚠️ No plan found for agent confirmation")
                    await self.send_error_response("No plan found")
                    return
            
            # Handle as button action
            await self._handle_button_action(button_action)
            
        except Exception as e:
            logger.error(f"❌ Error handling agent confirmation: {e}")
            await self.send_error_response(str(e))

    async def _handle_overlay_session(self, message: Dict[str, Any]) -> None:
        """Handle overlay session messages"""
        try:
            # Extract required fields
            session_id = message.get("session_id")
            if not session_id:
                logger.warning("⚠️ Missing session_id in overlay session")
                await self.send_error_response("Missing session_id")
                return
            
            # Store session info
            self.sessions[session_id] = {
                "last_active": time.time(),
                "metadata": message.get("metadata", {})
            }
            
            # Send acknowledgment
            await self.send_response({
                "type": "overlay_session_response",
                "success": True,
                "session_id": session_id,
                "message": "Session registered successfully"
            })
            
        except Exception as e:
            logger.error(f"❌ Error handling overlay session: {e}")
            await self.send_error_response(str(e))

    async def send_response(self, response: Dict[str, Any]) -> None:
        """Send a response to the client"""
        try:
            if self.ws:
                await self.ws.send(json.dumps(response))
        except Exception as e:
            logger.error(f"❌ Error sending response: {e}")

    async def send_error_response(self, error_message: str) -> None:
        """Send an error response to the client"""
        try:
            await self.send_response({
                "type": "error",
                "success": False,
                "error": error_message
            })
        except Exception as e:
            logger.error(f"❌ Error sending error response: {e}")
            
    async def _handle_chat_request(self, message: Dict[str, Any]) -> None:
        """Handle chat request messages"""
        try:
            # Extract required fields
            query = message.get("query")
            mode = message.get("mode", "general").lower()
            timestamp = message.get("timestamp", str(int(time.time())))
            
            if not query:
                logger.warning("⚠️ Missing query in chat request")
                await self.send_error_response("Missing query")
                return
            
            # For debugging
            logger.info(f"📝 Chat request received: {query[:50]}... (mode: {mode})")
            
            # Process the chat request
            # This is a placeholder - replace with your actual implementation
            response_content = f"This is a response to your query: {query}"
            
            # Send response
            await self.send_response({
                "type": "chat_response",
                "payload": {
                    "success": True,
                    "response": response_content,
                    "mode": mode.upper(),
                    "processing_time": 0.5,
                },
                "timestamp": str(int(time.time()))
            })
            
        except Exception as e:
            logger.error(f"❌ Error handling chat request: {e}")
            await self.send_error_response(str(e))
    
    async def _handle_chat_response(self, message: Dict[str, Any]) -> None:
        """Handle chat response messages (for passing responses between services)"""
        try:
            # This handler processes chat_response messages received from another service
            # that may need to be forwarded to clients
            
            # Extract required fields
            payload = message.get("payload", {})
            client_id = message.get("client_id")
            
            if not payload:
                logger.warning("⚠️ Missing payload in chat response")
                await self.send_error_response("Missing payload")
                return
            
            # Log receipt of response
            logger.info(f"📝 Chat response received from service for client: {client_id}")
            
            # Forward to client if needed - this depends on your architecture
            # This is a placeholder implementation
            await self.send_response({
                "type": "chat_response",
                "payload": payload,
                "timestamp": str(int(time.time()))
            })
            
        except Exception as e:
            logger.error(f"❌ Error handling chat response: {e}")
            await self.send_error_response(str(e)) 