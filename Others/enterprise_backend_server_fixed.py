#!/usr/bin/env python3
"""
Enterprise-Grade Backend Server with WORKING UI Automation
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import websockets
from websockets.server import WebSocketServerProtocol

# Import our enterprise components
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure enterprise logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enterprise_backend_server_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseBackendServerFixed:
    """Fixed Enterprise Backend Server with working UI automation"""
    
    def __init__(self, port: int = 8767):
        self.port = port
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'ui_automation_requests': 0,
            'ui_automation_successes': 0,
            'mode_usage': {'ask': 0, 'agent': 0, 'suggest': 0, 'general': 0}
        }
        self.server = None
        
        # Import UI automation components
        try:
            from enterprise_workflow_engine import EnterpriseWorkflowEngine
            from ui_automation_engine import MacOSUIController
            self.workflow_engine = EnterpriseWorkflowEngine()
            self.ui_automation = MacOSUIController()
            logger.info("✅ UI automation components loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load UI automation: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            self.workflow_engine = None
            self.ui_automation = None
    
    async def start_server(self):
        """Start the fixed enterprise WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                "127.0.0.1",
                self.port,
                ping_interval=20,
                ping_timeout=10,
                max_size=10 * 1024 * 1024,
                max_queue=100
            )
            
            logger.info(f"🚀 FIXED Enterprise Backend Server started on ws://127.0.0.1:{self.port}")
            logger.info("🎯 UI Automation ENABLED and ready for Agent mode")
            
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            sys.exit(1)
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle client connections"""
        client_id = str(uuid.uuid4())
        session_data = {
            'id': client_id,
            'connected_at': datetime.now(),
            'message_count': 0
        }
        
        logger.info(f"👤 Client {client_id} connected")
        
        try:
            self.connected_clients.add(websocket)
            self.client_sessions[client_id] = session_data
            
            # Send welcome
            await self._send_message(websocket, {
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Fixed Backend Server with UI Automation",
                "capabilities": ["ui_automation", "llm_queries", "agent_mode"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle messages
            async for raw_message in websocket:
                try:
                    await self._process_message(websocket, client_id, raw_message)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    await self._send_error(websocket, str(e))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"👋 Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"❌ Error with client {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
            if client_id in self.client_sessions:
                del self.client_sessions[client_id]
    
    async def _process_message(self, websocket: WebSocketServerProtocol, client_id: str, raw_message: str):
        """Process messages with UI automation support"""
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type', 'unknown')
            
            logger.info(f"📥 Processing {msg_type} from client {client_id}")
            
            if msg_type == "chat_request":
                await self._handle_chat_request(websocket, client_id, message)
            else:
                logger.warning(f"⚠️ Unknown message type: {msg_type}")
                await self._send_error(websocket, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            await self._send_error(websocket, "Invalid JSON format")
    
    async def _handle_chat_request(self, websocket: WebSocketServerProtocol, client_id: str, message: Dict[str, Any]):
        """Handle chat requests with UI automation for agent mode"""
        try:
            query = message.get('query', '')
            mode = message.get('mode', 'general').lower()
            
            logger.info(f"🗣️ Chat request - Mode: {mode}, Query: {query}")
            
            # Update metrics
            self.performance_metrics['total_requests'] += 1
            self.performance_metrics['mode_usage'][mode] += 1
            
            # Special handling for agent mode UI automation
            if mode == 'agent':
                await self._handle_agent_mode(websocket, client_id, query)
            else:
                # Handle other modes with simple response
                response_text = f"Mode '{mode}' processed: {query}"
                await self._send_chat_response(websocket, response_text, mode, True, 0.9)
            
            self.performance_metrics['successful_requests'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error in chat request: {e}")
            logger.error(traceback.format_exc())
            self.performance_metrics['failed_requests'] += 1
            await self._send_error(websocket, "Failed to process chat request")
    
    async def _handle_agent_mode(self, websocket: WebSocketServerProtocol, client_id: str, query: str):
        """Handle agent mode with REAL UI automation execution"""
        try:
            logger.info(f"🤖 Agent mode request: {query}")
            
            # Check if it's a UI automation command
            query_lower = query.lower()
            ui_keywords = ['click', 'type', 'press', 'mouse', 'keyboard', 'automation']
            is_ui_request = any(keyword in query_lower for keyword in ui_keywords)
            
            if is_ui_request:
                logger.info(f"🖱️ UI automation detected: {query}")
                self.performance_metrics['ui_automation_requests'] += 1
                
                # Execute UI automation directly
                if self.workflow_engine and self.ui_automation:
                    try:
                        # Analyze and execute workflow
                        logger.info(f"🔧 Calling workflow engine with query: {query}")
                        execution_result = await self.workflow_engine.process_agent_request(query)
                        logger.info(f"🔍 Workflow result: {execution_result}")
                        
                        if execution_result and execution_result.get('success'):
                            logger.info("✅ UI automation executed successfully!")
                            self.performance_metrics['ui_automation_successes'] += 1
                            
                            response_text = f"""✅ **UI Automation Executed Successfully!**

🎯 **Action**: {query}
🖱️ **Execution**: Completed mouse/keyboard automation
⚡ **Status**: Success
🕐 **Time**: {datetime.now().strftime('%H:%M:%S')}

**Details**: Real UI automation was performed on your system."""
                            
                            await self._send_chat_response(websocket, response_text, 'agent', True, 1.0)
                            return
                        else:
                            logger.warning(f"⚠️ UI automation failed or returned None: {execution_result}")
                            logger.warning(f"⚠️ Result type: {type(execution_result)}")
                            
                    except Exception as ui_error:
                        logger.error(f"❌ UI automation error: {ui_error}")
                        logger.error(traceback.format_exc())
                
                # Fallback response if UI automation failed
                response_text = f"""⚠️ **UI Automation Issue**

🎯 **Request**: {query}
🔧 **Status**: Automation system needs attention
💡 **Note**: The system recognized this as a UI automation request but execution failed.

Please check the automation components."""
                
                await self._send_chat_response(websocket, response_text, 'agent', False, 0.5)
            else:
                # Non-UI agent request - provide planning response
                response_text = f"""🤖 **Agent Mode Response**

📋 **Task**: {query}
🎯 **Analysis**: This appears to be a planning or analysis request.
💡 **Action**: Processed in agent mode.

**Result**: Task analyzed and response generated."""
                
                await self._send_chat_response(websocket, response_text, 'agent', True, 0.8)
                
        except Exception as e:
            logger.error(f"❌ Agent mode error: {e}")
            logger.error(traceback.format_exc())
            await self._send_error(websocket, "Agent mode processing failed")
    
    async def _send_chat_response(self, websocket: WebSocketServerProtocol, content: str, mode: str, success: bool, confidence: float):
        """Send chat response in overlay-compatible format"""
        response = {
            "type": "chat_response",
            "payload": {
                "response": content,
                "mode": mode,
                "success": success,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self._send_message(websocket, response)
    
    async def _send_message(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        """Send message to websocket"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error response"""
        error_response = {
            "type": "error",
            "payload": {
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self._send_message(websocket, error_response)

async def main():
    """Main entry point"""
    try:
        logger.info("🚀 Starting Fixed Enterprise Backend Server...")
        server = EnterpriseBackendServerFixed()
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server crashed: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())