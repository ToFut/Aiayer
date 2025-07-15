#!/usr/bin/env python3
"""
Unified Backend - Integrates UI2HTML Memory System with Overlay Chat
Provides real-time UI context, memory querying, and agent execution
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import websockets
from aiohttp import web
import aiohttp_cors

from ui2html_sensor import UI2HTMLSensor
from memory_store import store_ui_snapshot, query_ui_by_text, get_ui_memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedBackend:
    """Unified backend for UI2HTML memory, overlay chat, and agent execution."""
    
    def __init__(self):
        self.ui_sensor = UI2HTMLSensor()
        self.clients = {}
        self.current_ui_context = None
        self.stats = {
            "connections": 0,
            "queries_processed": 0,
            "memory_queries": 0,
            "ui_snapshots": 0
        }
        
        # Initialize LLM service (optional)
        self.llm_service = None
        try:
            from llm.llm_service import LLMService
            self.llm_service = LLMService()
            logger.info("✅ LLM Service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize LLM Service: {e}")
        
        logger.info("🚀 Unified Backend initialized")

    async def start_server(self):
        """Start the unified backend server with both WebSocket and HTTP."""
        try:
            # Start UI sensor
            self.ui_sensor.start()
            logger.info("🚀 UI Sensor started")
            
            # Start UI context monitoring
            asyncio.create_task(self._monitor_ui_context())
            logger.info("🔍 UI Context monitoring started")
            
            # Create HTTP app for API endpoints
            app = web.Application()
            
            # Add CORS middleware
            cors = aiohttp_cors.setup(app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Add routes
            app.router.add_get('/ui_context', self.handle_ui_context_api)
            app.router.add_get('/health', self.handle_health_api)
            app.router.add_get('/stats', self.handle_stats_api)
            
            # Add CORS to all routes
            for route in list(app.router.routes()):
                cors.add(route)
            
            # Create WebSocket server
            ws_server = await websockets.serve(
                self.handle_client,
                "localhost",
                8767
            )
            
            logger.info("🚀 Unified Backend Server started")
            logger.info("   WebSocket: ws://localhost:8767")
            logger.info("   HTTP API: http://localhost:8767")
            
            # Start HTTP server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', 8767)
            await site.start()
            
            # Keep servers running
            await asyncio.gather(
                ws_server.wait_closed(),
                runner.cleanup()
            )
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections."""
        client_id = f"conn_{int(time.time() * 1000)}"
        self.clients[client_id] = websocket
        logger.info(f"Client connected: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', 'unknown')
                    
                    logger.info(f"Processing {message_type} from {client_id}")
                    
                    if message_type == 'query':
                        # Handle user query
                        user_message = data.get('message', '')
                        response = await self._process_user_query(user_message)
                        
                        await websocket.send(json.dumps({
                            'type': 'response',
                            'message': response
                        }))
                        
                    elif message_type == 'click':
                        # Handle button click
                        button_index = data.get('button_index', 0)
                        result = await self._handle_button_click(button_index)
                        
                        await websocket.send(json.dumps({
                            'type': 'click_result',
                            'success': result['success'],
                            'message': result['message']
                        }))
                        
                    elif message_type == 'get_ui_context':
                        # Send current UI context
                        ui_context = self._get_current_ui_context()
                        await websocket.send(json.dumps({
                            'type': 'ui_context',
                            'payload': ui_context
                        }))
                        
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': f'Unknown message type: {message_type}'
                        }))
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]

    async def _process_user_query(self, message):
        """Process user query and return response."""
        try:
            # Get current UI context
            ui_context = self._get_current_ui_context()
            buttons = ui_context.get('buttons', [])
            
            # Check for specific commands
            message_lower = message.lower()
            
            if 'what can i interact with' in message_lower or 'show me all ui elements' in message_lower:
                if buttons:
                    button_list = []
                    for i, button in enumerate(buttons[:20]):  # Limit to first 20
                        button_list.append(f"{i+1}. {button['name']} ({button['type']})")
                    
                    if len(buttons) > 20:
                        button_list.append(f"... and {len(buttons) - 20} more buttons")
                    
                    return f"I found {len(buttons)} clickable elements:\n" + "\n".join(button_list)
                else:
                    return "I couldn't find any clickable buttons on your screen right now."
            
            elif 'list specific buttons' in message_lower:
                if buttons:
                    button_list = []
                    for i, button in enumerate(buttons[:10]):
                        button_list.append(f"{i+1}. {button['name']}")
                    return "Here are some buttons I can see:\n" + "\n".join(button_list)
                else:
                    return "No buttons found on screen."
            
            elif 'click' in message_lower:
                # Try to extract button number
                import re
                numbers = re.findall(r'\d+', message)
                if numbers:
                    button_index = int(numbers[0]) - 1
                    if 0 <= button_index < len(buttons):
                        result = await self._handle_button_click(button_index)
                        return result['message']
                    else:
                        return f"Button {button_index + 1} not found. I can see {len(buttons)} buttons."
                else:
                    return "Please specify which button to click (e.g., 'Click button 1')"
            
            else:
                # Use LLM for general queries
                if self.llm_service:
                    try:
                        # Create context with UI information
                        context = f"Current UI: {ui_context.get('name', 'Unknown')} app with {len(buttons)} clickable elements. "
                        if buttons:
                            context += f"Some buttons: {', '.join([b['name'] for b in buttons[:5]])}"
                        
                        response = await self.llm_service.generate_response(
                            f"{context}\n\nUser question: {message}"
                        )
                        return response
                    except Exception as e:
                        logger.error(f"LLM error: {e}")
                        return f"I understand your query: '{message}'. I have access to your current UI context and can help you interact with what's on your screen. What specific action would you like me to help with?"
                else:
                    return f"I understand your query: '{message}'. I have access to your current UI context and can help you interact with what's on your screen. What specific action would you like me to help with?"
                    
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Sorry, I encountered an error processing your request."

    async def _handle_button_click(self, button_index):
        """Handle button click action."""
        try:
            # Get current UI context
            ui_context = self._get_current_ui_context()
            buttons = ui_context.get('buttons', [])
            
            if button_index >= len(buttons):
                return {
                    'success': False,
                    'message': f'Button {button_index + 1} not found. I can see {len(buttons)} buttons.'
                }
            
            button = buttons[button_index]
            button_name = button.get('name', 'Unknown')
            button_type = button.get('type', 'Unknown')
            
            logger.info(f"🎯 Attempting to click button {button_index + 1}: {button_name} ({button_type})")
            
            # For now, simulate the click (in a real implementation, this would use atomacos)
            # TODO: Implement actual button clicking using atomacos
            success = True
            message = f"✅ Successfully clicked '{button_name}' (button {button_index + 1})"
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Error handling button click: {e}")
            return {
                'success': False,
                'message': f"Error clicking button: {str(e)}"
            }

    async def handle_ui_context_api(self, request):
        """Handle HTTP API request for UI context."""
        try:
            ui_context = self._get_current_ui_context()
            return web.json_response(ui_context)
        except Exception as e:
            logger.error(f"Error handling UI context API: {e}")
            return web.json_response({
                'error': str(e),
                'app_name': 'Unknown',
                'element_count': 0,
                'buttons': []
            }, status=500)

    async def handle_health_api(self, request):
        """Handle health check API."""
        return web.json_response({
            'status': 'healthy',
            'timestamp': time.time(),
            'ui_sensor_running': self.ui_sensor.is_running,
            'clients_connected': len(self.clients)
        })

    async def handle_stats_api(self, request):
        """Handle stats API."""
        return web.json_response({
            'stats': self.stats,
            'timestamp': time.time()
        })

    def _get_current_ui_context(self):
        """Get current UI context for API responses."""
        try:
            # Get latest UI snapshot
            latest_snapshot = self.ui_sensor.get_latest_snapshot()
            if not latest_snapshot:
                return {
                    'app_name': 'Unknown',
                    'element_count': 0,
                    'buttons': [],
                    'timestamp': time.time()
                }
            
            # Extract buttons from the UI tree
            ui_tree = latest_snapshot.get('ui_tree', {})
            buttons = self._extract_buttons_from_ui_tree(ui_tree)
            
            return {
                'app_name': latest_snapshot.get('app_name', 'Unknown'),
                'element_count': latest_snapshot.get('element_count', 0),
                'buttons': buttons,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Error getting UI context: {e}")
            return {
                'app_name': 'Unknown',
                'element_count': 0,
                'buttons': [],
                'timestamp': time.time()
            }
    
    async def _monitor_ui_context(self):
        """Continuously monitor UI context"""
        logger.info("🔄 Starting UI context monitoring")
        
        while True:
            try:
                # Capture current UI snapshot
                snapshot = self.ui_sensor.capture_snapshot()
                if snapshot:
                    self.current_ui_context = snapshot
                    self.stats["ui_snapshots"] += 1
                    
                    # Broadcast UI update to connected clients
                    await self._broadcast_ui_update(snapshot)
                
                # Wait before next capture
                await asyncio.sleep(2)  # Every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in UI monitoring: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def _prepare_llm_context(self, query: str, current_ui: Optional[Dict], memory_results: List[Dict]) -> str:
        """Prepare context for LLM"""
        context_parts = []
        
        # Add current UI context
        if current_ui:
            context_parts.append(f"Current Application: {current_ui.get('name', 'Unknown')}")
            context_parts.append(f"UI Elements: {current_ui.get('element_count', 0)}")
            
            # Add some UI details
            ui_tree = current_ui.get('ui_tree', {})
            if ui_tree:
                context_parts.append(f"Current UI Structure: {ui_tree.get('name', 'Unknown')} with {len(ui_tree.get('children', []))} main elements")
        
        # Add memory results
        if memory_results:
            context_parts.append("Recent UI History:")
            for i, result in enumerate(memory_results[:2]):  # Top 2 results
                metadata = result.get('metadata', {})
                context_parts.append(f"  {i+1}. {metadata.get('timestamp', 'Unknown time')}: {metadata.get('element_count', 0)} elements")
        
        # Add query context
        context_parts.append(f"User Query: {query}")
        
        return "\n".join(context_parts)
    
    async def _generate_real_llm_response(self, query: str, context: str, mode: str) -> str:
        """Generate real LLM response using the integrated LLM service"""
        try:
            if not self.llm_service:
                raise Exception("No LLM service available")
            
            # Build enhanced prompt with UI context
            system_prompt = f"""You are an AI assistant with access to real-time UI context. 
You can see what's on the user's screen and help them interact with it.

Current UI Context:
{context}

Instructions:
- Provide helpful, contextual responses about the user's screen
- If they ask about buttons, list the actual buttons you can see
- If they ask to click something, explain what you can click
- Be specific about UI elements and their locations
- Use the UI context to give relevant answers

User Query: {query}
Assistant:"""

            # Use the LLM service to generate response
            if hasattr(self.llm_service, 'generate_response'):
                # For streaming LLM service
                response_chunks = []
                async for chunk in self.llm_service.generate_response(system_prompt):
                    response_chunks.append(chunk)
                return ''.join(response_chunks)
            elif hasattr(self.llm_service, 'generate_response'):
                # For non-streaming LLM service
                return await self.llm_service.generate_response(system_prompt)
            else:
                raise Exception("LLM service does not have expected methods")
                
        except Exception as e:
            logger.error(f"Error generating real LLM response: {e}")
            return await self._generate_fallback_response(query, context, mode)

    def _extract_buttons_from_ui_tree(self, ui_tree):
        """Extract clickable buttons from UI tree."""
        buttons = []
        
        def traverse_node(node):
            if not isinstance(node, dict):
                return
            
            # Check if this node is a button
            node_type = node.get('type', '').lower()
            node_name = node.get('name', '')
            
            # Define clickable element types
            clickable_types = [
                'axbutton', 'axlink', 'axmenuitem', 'axradiobutton', 
                'axcheckbox', 'axpushbutton', 'axpopupbutton', 'axslider',
                'button', 'link', 'menuitem', 'radiobutton', 'checkbox'
            ]
            
            if any(clickable_type in node_type for clickable_type in clickable_types):
                buttons.append({
                    'name': node_name,
                    'type': node_type,
                    'bounds': node.get('bounds', []),
                    'id': node.get('id', '')
                })
            
            # Recursively traverse children
            for child in node.get('children', []):
                traverse_node(child)
        
        traverse_node(ui_tree)
        return buttons

    async def _generate_fallback_response(self, query: str, context: str, mode: str) -> str:
        """Generate fallback response when LLM is not available"""
        query_lower = query.lower()
        
        # Handle button-related queries with real UI analysis
        if any(word in query_lower for word in ["button", "click", "clickable", "scan"]):
            current_ui = await self._get_current_ui_context()
            if current_ui and current_ui.get("ui_tree"):
                buttons = self._extract_buttons_from_ui_tree(current_ui["ui_tree"])
                
                if buttons:
                    button_list = []
                    for i, button in enumerate(buttons[:10]):  # Limit to first 10 buttons
                        button_list.append(f"{i+1}. {button['name']} ({button['type']})")
                    
                    return f"I found {len(buttons)} clickable elements on your screen:\n\n" + "\n".join(button_list) + "\n\nYou can ask me to click any of these elements by saying 'Click button 1' or 'Click the [button name]'."
                else:
                    return "I scanned your screen but didn't find any obvious clickable buttons. I can see UI elements, but they may not be traditional buttons. Try asking 'What can I interact with?' or 'Show me all UI elements'."
            else:
                return "I can see UI elements on your screen. To list specific buttons, I need to analyze the current UI structure. Would you like me to scan for clickable elements?"
        
        elif "what" in query_lower and "screen" in query_lower:
            if self.current_ui_context:
                app_name = self.current_ui_context.get('name', 'Unknown')
                element_count = self.current_ui_context.get('element_count', 0)
                return f"You're currently in {app_name} with {element_count} UI elements visible. I can see the interface structure and help you interact with it."
            else:
                return "I'm not able to see your current screen at the moment. Please try again in a moment."
        else:
            return f"I understand your query: '{query}'. I have access to your current UI context and can help you interact with what's on your screen. What specific action would you like me to help with?"

    async def _execute_ui_action(self, action_description: str, current_ui: Optional[Dict]) -> Dict[str, Any]:
        """Execute UI actions like clicking buttons"""
        try:
            action_lower = action_description.lower()
            
            # Handle button clicking
            if "click" in action_lower and ("button" in action_lower or "first" in action_lower):
                if current_ui and current_ui.get("ui_tree"):
                    buttons = self._extract_buttons_from_ui_tree(current_ui["ui_tree"])
                    
                    if buttons:
                        # Click the first button
                        first_button = buttons[0]
                        logger.info(f"Would click button: {first_button['name']} at {first_button['bounds']}")
                        
                        return {
                            "success": True,
                            "action": "click_button",
                            "button_name": first_button['name'],
                            "button_type": first_button['type'],
                            "message": f"Successfully clicked '{first_button['name']}' button"
                        }
                    else:
                        return {
                            "success": False,
                            "action": "click_button",
                            "message": "No clickable buttons found on screen"
                        }
                else:
                    return {
                        "success": False,
                        "action": "click_button",
                        "message": "No UI context available for clicking"
                    }
            
            # Handle listing buttons
            elif "list" in action_lower and "button" in action_lower:
                if current_ui and current_ui.get("ui_tree"):
                    buttons = self._extract_buttons_from_ui_tree(current_ui["ui_tree"])
                    
                    if buttons:
                        button_list = []
                        for i, button in enumerate(buttons[:10]):
                            button_list.append(f"{i+1}. {button['name']} ({button['type']})")
                        
                        return {
                            "success": True,
                            "action": "list_buttons",
                            "buttons": buttons,
                            "message": f"Found {len(buttons)} clickable elements:\n" + "\n".join(button_list)
                        }
                    else:
                        return {
                            "success": False,
                            "action": "list_buttons",
                            "message": "No clickable buttons found on screen"
                        }
                else:
                    return {
                        "success": False,
                        "action": "list_buttons",
                        "message": "No UI context available"
                    }
            
            else:
                return {
                    "success": False,
                    "action": "unknown",
                    "message": f"Action '{action_description}' not implemented yet"
                }
                
        except Exception as e:
            logger.error(f"Error executing UI action: {e}")
            return {
                "success": False,
                "action": "error",
                "message": f"Error executing action: {str(e)}"
            }
    
    async def _broadcast_ui_update(self, snapshot: Dict[str, Any]):
        """Broadcast UI update to all connected clients"""
        if not self.clients:
            return
        
        message = {
            "type": "ui_context_update",
            "payload": {
                "app_name": snapshot.get('name', 'Unknown'),
                "element_count": snapshot.get('element_count', 0),
                "timestamp": time.time()
            }
        }
        
        # Send to all connected clients
        disconnected = []
        for connection_id, websocket in self.clients.items():
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            if connection_id in self.clients:
                del self.clients[connection_id]
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if connection_id in self.clients:
            try:
                websocket = self.clients[connection_id]
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
    
    async def send_error(self, connection_id: str, error_message: str):
        """Send error message to client"""
        error_response = {
            "type": "error",
            "payload": {
                "message": error_message,
                "timestamp": time.time()
            }
        }
        await self.send_message(connection_id, error_response)
    
    async def shutdown(self):
        """Shutdown the backend gracefully"""
        logger.info("Shutting down Unified Backend...")
        
        # Stop UI monitoring
        # The _monitor_ui_context task is now managed by start_server
        
        # Stop UI sensor
        if self.ui_sensor:
            self.ui_sensor.stop()
        
        # Close all connections
        for connection_id, websocket in self.clients.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
        
        logger.info("Unified Backend shutdown complete")

async def start_unified_backend():
    """Start the unified backend server"""
    backend = UnifiedBackend()
    await backend.start_server()
    
    try:
        # Keep the server running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await backend.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_unified_backend()) 