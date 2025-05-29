#!/usr/bin/env python3
"""
Web-based AgentMode Coordination Test Server
Serves the test dashboard and handles WebSocket connections for real-time testing
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Set
import websockets
import http.server
import socketserver
import threading
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoordinationTestServer:
    """Web server for coordination testing with WebSocket support"""
    
    def __init__(self, port=8080, ws_port=8765):
        self.port = port
        self.ws_port = ws_port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.current_plans: Dict[str, Any] = {}
        
    async def start_servers(self):
        """Start both HTTP and WebSocket servers"""
        # Start WebSocket server with proper handler signature
        async def websocket_handler(websocket):
            await self.handle_websocket(websocket, "/")
        
        ws_server = await websockets.serve(
            websocket_handler,
            "localhost",
            self.ws_port
        )
        logger.info(f"🔌 WebSocket server started on ws://localhost:{self.ws_port}")
        
        # Start HTTP server in a separate thread
        http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        http_thread.start()
        logger.info(f"🌐 HTTP server started on http://localhost:{self.port}")
        
        logger.info("🚀 Coordination test servers running!")
        logger.info(f"📱 Open http://localhost:{self.port}/web_coordination_test.html to begin testing")
        
        # Keep running
        await ws_server.wait_closed()
    
    def start_http_server(self):
        """Start HTTP server for serving the test page"""
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress HTTP logs to keep console clean
                pass
        
        with socketserver.TCPServer(("", self.port), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"🔗 Client connected from {client_addr}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "message": "Connected to AgentMode coordination backend",
                "timestamp": time.time()
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {client_addr}")
                except Exception as e:
                    logger.error(f"Error processing message from {client_addr}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client {client_addr} disconnected")
        finally:
            self.connected_clients.discard(websocket)
    
    async def process_message(self, websocket, data):
        """Process incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "create_plan":
            await self.handle_create_plan(websocket, data)
        elif message_type == "execute_plan":
            await self.handle_execute_plan(websocket, data)
        elif message_type == "ping":
            await websocket.send(json.dumps({"type": "pong", "timestamp": time.time()}))
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def handle_create_plan(self, websocket, data):
        """Handle automation plan creation requests"""
        message = data.get("message", "")
        mode = data.get("mode", "agent")
        session_id = data.get("session_id", f"session_{int(time.time())}")
        
        logger.info(f"📝 Creating {mode} plan for: '{message}'")
        
        try:
            # Try to use real automation handler
            from real_agent_automation_handler import real_agent_handler
            
            start_time = time.time()
            result = await real_agent_handler.handle_agent_request(message, session_id)
            creation_time = time.time() - start_time
            
            if result["success"]:
                plan_id = result.get("plan_id")
                if plan_id and plan_id in real_agent_handler.active_plans:
                    plan = real_agent_handler.active_plans[plan_id]
                    
                    # Store plan reference
                    self.current_plans[plan_id] = {
                        "plan": plan,
                        "session_id": session_id,
                        "creation_time": creation_time
                    }
                    
                    # Send plan to client
                    await websocket.send(json.dumps({
                        "type": "plan_created",
                        "plan": {
                            "task_id": plan.task_id,
                            "title": plan.title,
                            "description": plan.description,
                            "steps": [
                                {
                                    "id": step.id,
                                    "description": step.description,
                                    "action_type": step.action_type,
                                    "confidence": step.confidence
                                }
                                for step in plan.steps
                            ],
                            "estimated_duration": plan.estimated_duration,
                            "ai_powered": getattr(plan, 'llm_generated', False)
                        },
                        "creation_time": creation_time,
                        "automation_available": result.get("automation_available", False)
                    }))
                    
                    logger.info(f"✅ Plan created successfully in {creation_time:.2f}s")
                else:
                    raise Exception("Plan created but not found in active plans")
            else:
                raise Exception(result.get("response", "Plan creation failed"))
                
        except Exception as e:
            logger.error(f"❌ Plan creation failed: {e}")
            
            # Send error to client
            await websocket.send(json.dumps({
                "type": "plan_error",
                "error": str(e),
                "message": "Plan creation failed - check backend connection"
            }))
    
    async def handle_execute_plan(self, websocket, data):
        """Handle plan execution requests"""
        plan_id = data.get("plan_id")
        session_id = data.get("session_id", f"session_{int(time.time())}")
        
        if not plan_id or plan_id not in self.current_plans:
            await websocket.send(json.dumps({
                "type": "execution_error",
                "error": "Plan not found or expired"
            }))
            return
        
        logger.info(f"🚀 Executing plan: {plan_id}")
        
        try:
            # Get real automation handler
            from real_agent_automation_handler import real_agent_handler
            
            # Send execution start notification
            await websocket.send(json.dumps({
                "type": "execution_started",
                "plan_id": plan_id,
                "timestamp": time.time()
            }))
            
            # Execute the plan
            start_time = time.time()
            result = await real_agent_handler.handle_button_action(
                action="execute_plan",
                plan_id=plan_id,
                session_id=session_id
            )
            execution_time = time.time() - start_time
            
            if result["success"]:
                # Send completion notification
                await websocket.send(json.dumps({
                    "type": "execution_complete",
                    "plan_id": plan_id,
                    "execution_time": execution_time,
                    "success_rate": result.get("success_rate", 0),
                    "steps_executed": result.get("steps_executed", 0),
                    "steps_failed": result.get("steps_failed", 0),
                    "response": result.get("response", "Execution completed")
                }))
                
                logger.info(f"✅ Plan executed successfully in {execution_time:.2f}s")
                
                # Clean up
                if plan_id in self.current_plans:
                    del self.current_plans[plan_id]
            else:
                raise Exception(result.get("response", "Execution failed"))
                
        except Exception as e:
            logger.error(f"❌ Plan execution failed: {e}")
            
            await websocket.send(json.dumps({
                "type": "execution_error",
                "plan_id": plan_id,
                "error": str(e)
            }))
    
    async def broadcast_message(self, message):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            disconnected = set()
            for client in self.connected_clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.connected_clients.discard(client)

async def main():
    """Main server function"""
    print("🤖 AgentMode Coordination Test Server")
    print("=" * 50)
    
    server = CoordinationTestServer(port=8080, ws_port=8765)
    
    try:
        await server.start_servers()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("\n💡 Try running: pip install websockets")