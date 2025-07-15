#!/usr/bin/env python3
"""
Simple Backend - Basic working version for UI2HTML memory system
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
import websockets

from ui2html_sensor import UI2HTMLSensor
from memory_store import store_ui_snapshot, query_ui_by_text, get_ui_memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBackend:
    """Simple backend for UI2HTML memory system."""
    
    def __init__(self):
        self.ui_sensor = UI2HTMLSensor()
        self.clients = {}
        self.current_ui_context = None
        self.stats = {
            "connections": 0,
            "queries_processed": 0,
            "ui_snapshots": 0
        }
        
        logger.info("🚀 Simple Backend initialized")

    async def start_server(self):
        """Start the WebSocket server."""
        try:
            # Start UI sensor
            self.ui_sensor.start()
            logger.info("🚀 UI Sensor started")
            
            # Start UI context monitoring
            asyncio.create_task(self._monitor_ui_context())
            logger.info("🔍 UI Context monitoring started")
            
            # Create WebSocket server
            server = await websockets.serve(
                self.handle_client,
                "localhost",
                8767
            )
            
            logger.info("🚀 Simple Backend Server started on ws://localhost:8767")
            
            # Keep server running
            await server.wait_closed()
            
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
            
            else:
                return f"I understand your query: '{message}'. I have access to your current UI context and can help you interact with what's on your screen. What specific action would you like me to help with?"
                    
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Sorry, I encountered an error processing your request."

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

    async def _broadcast_ui_update(self, snapshot):
        """Broadcast UI update to all connected clients."""
        if not self.clients:
            return
        
        try:
            ui_context = self._get_current_ui_context()
            message = {
                'type': 'ui_context_update',
                'payload': ui_context
            }
            
            # Send to all connected clients
            disconnected_clients = []
            for client_id, websocket in self.clients.items():
                try:
                    await websocket.send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Remove disconnected clients
            for client_id in disconnected_clients:
                del self.clients[client_id]
                
        except Exception as e:
            logger.error(f"Error broadcasting UI update: {e}")

async def start_simple_backend():
    """Start the simple backend server."""
    backend = SimpleBackend()
    await backend.start_server()

if __name__ == "__main__":
    asyncio.run(start_simple_backend()) 