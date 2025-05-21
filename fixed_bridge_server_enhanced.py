#!/usr/bin/env python3
"""
Enhanced Bridge Server
Provides a central communication hub for routing sensor data to memory system
with proper prioritization and message handling.
"""

import asyncio
import websockets
import json
import logging
import os
import time
import traceback
from typing import Dict, List, Any, Set, Optional
from datetime import datetime
import signal
import sys

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Connection constants
WS_PORT = 8768  # Changed from 8765 to avoid port conflict
MEMORY_SERVER_PORT = 8769  # Changed from 8766 to avoid port conflict
PID_FILE = "pids/bridge_server.pid"

class EnhancedBridgeServer:
    """
    Enhanced Bridge Server that properly routes sensor data to memory components
    with priorities and dedicated connection types.
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = WS_PORT):
        self.host = host
        self.port = port
        self.clients: Dict[str, Set[websockets.WebSocketServerProtocol]] = {
            'sensor': set(),       # Sensor clients that send data
            'memory': set(),       # Memory clients that receive data
            'llm': set(),          # LLM service clients
            'ui': set(),           # UI/Overlay clients
            'application': set(),  # Application clients
            'other': set()         # Miscellaneous clients
        }
        self.client_states = {}  # Track client connection states
        self.sensor_data_buffers: Dict[str, List[Dict[str, Any]]] = {
            'screen': [],
            'process': [],
            'file': []
        }
        self.max_buffer_size = 10  # Max items in buffer per sensor type
        self.server = None
        self.process_task = None
        self.stopping = False
        
        # Track statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'last_activity': time.time(),
            'clients_connected': 0,
            'start_time': time.time()
        }
        
        # Set up PID directory
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"Enhanced Bridge Server initialized on {host}:{port}")
        logger.info(f"PID {os.getpid()} written to {PID_FILE}")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        if not self.stopping:
            self.stopping = True
            asyncio.create_task(self.stop())
    
    async def start(self):
        """Start the WebSocket server"""
        try:
            logger.info(f"Starting Enhanced Bridge Server on {self.host}:{self.port}")
            
            # Start the WebSocket server with more lenient timeouts
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=90,   # Wait 90 seconds for pong response
                close_timeout=30,  # Increased close timeout
                max_size=10 * 1024 * 1024,  # 10MB max message size
                max_queue=32,  # Maximum number of messages in queue
                compression=None  # Disable compression for better performance
            )
            
            # Start periodic tasks
            self.process_task = asyncio.create_task(self._periodic_tasks())
            
            logger.info(f"✅ Enhanced Bridge Server started successfully")
            
            # Keep the server running
            await self.server.wait_closed()
            
        except Exception as e:
            logger.error(f"❌ Error starting Enhanced Bridge Server: {e}")
            logger.error(traceback.format_exc())
            await self.stop()
    
    async def stop(self):
        """Stop the WebSocket server and clean up resources"""
        try:
            logger.info("Stopping Enhanced Bridge Server...")
            
            # Mark server as stopping
            self.stopping = True
            
            # Cancel periodic tasks
            if self.process_task and not self.process_task.done():
                self.process_task.cancel()
                try:
                    await self.process_task
                except asyncio.CancelledError:
                    pass
            
            # Close all client connections
            close_tasks = []
            for client_type, clients in self.clients.items():
                for ws in clients:
                    try:
                        close_tasks.append(ws.close(1001, "Server shutting down"))
                    except Exception as e:
                        logger.warning(f"Error closing {client_type} client: {e}")
            
            # Wait for connections to close
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            
            # Stop the server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            # Remove PID file
            try:
                os.remove(PID_FILE)
                logger.info(f"Removed PID file {PID_FILE}")
            except Exception as e:
                logger.warning(f"Error removing PID file: {e}")
            
            logger.info("✅ Enhanced Bridge Server stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Enhanced Bridge Server: {e}")
            logger.error(traceback.format_exc())
    
    async def _handle_connection(self, websocket):
        """Handle new WebSocket connections with client type registration"""
        client_type = "other"
        client_info = {
            "ip": websocket.remote_address[0] if websocket.remote_address else "unknown",
            "connected_at": datetime.now().isoformat(),
            "messages_received": 0,
            "messages_sent": 0,
            "last_activity": time.time(),
            "type": client_type,
            "last_ping": time.time()
        }
        
        # Store client state
        self.client_states[websocket] = client_info
        
        try:
            # Wait for client registration message
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle ping messages
                    if data.get('type') == 'ping':
                        client_info['last_ping'] = time.time()
                        try:
                            await websocket.send(json.dumps({
                                'type': 'pong',
                                'timestamp': time.time()
                            }))
                        except:
                            logger.debug("Error sending pong response, websocket may be closed")
                        continue
                    
                    # Handle pong messages
                    if data.get('type') == 'pong':
                        client_info['last_ping'] = time.time()
                        continue
                    
                    # Handle client registration
                    if data.get('type') == 'register' or data.get('type') == 'connection_established':
                        # Extract client type from either format
                        if data.get('type') == 'register':
                            client_type = data.get('client_type', 'other').lower()
                        else:  # connection_established
                            client_type = data.get('payload', {}).get('client', 'other').lower()
                            # Map legacy client types to new ones
                            if client_type in ['overlay', 'eye_widget_overlay', 'enhanced_eye_widget']:
                                client_type = 'ui'
                            elif client_type in ['enhanced_connector']:
                                client_type = 'application'
                        
                        if client_type not in self.clients:
                            logger.warning(f"Unknown client type: {client_type}, defaulting to 'other'")
                            client_type = 'other'
                        
                        # Add client to the appropriate set
                        self.clients[client_type].add(websocket)
                        client_info["type"] = client_type
                        
                        # Update stats
                        self.stats['clients_connected'] += 1
                        
                        # Send registration confirmation
                        try:
                            confirmation_msg = {
                                'type': 'registration_confirmed',
                                'client_type': client_type,
                                'status': 'success'
                            }
                            await websocket.send(json.dumps(confirmation_msg))
                            logger.info(f"Sent registration confirmation to {client_type} client: {json.dumps(confirmation_msg)}")
                        except Exception as e:
                            logger.error(f"Error sending registration confirmation: {e}")
                        
                        logger.info(f"Client registered as {client_type} from {client_info['ip']}")
                        break
                    else:
                        # If first message is not registration, send error and close connection
                        try:
                            error_msg = {
                                'type': 'error',
                                'message': 'Registration required before sending other messages'
                            }
                            logger.warning(f"Received non-registration message as first message: {message[:200]}...")
                            logger.warning(f"Sending error response: {json.dumps(error_msg)}")
                            await websocket.send(json.dumps(error_msg))
                            await websocket.close(1008, "Registration required")
                            logger.info(f"Closed connection due to missing registration from {client_info['ip']}")
                        except Exception as e:
                            logger.error(f"Error sending registration error: {e}")
                        return
                    
                except json.JSONDecodeError:
                    try:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON message'
                        }))
                    except:
                        logger.debug("Error sending JSON error, websocket may be closed")
                    self.stats['errors'] += 1
                except Exception as e:
                    logger.error(f"Error handling registration message: {e}")
                    self.stats['errors'] += 1
            
            # Process messages after registration
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    # Update client stats
                    client_info['messages_received'] += 1
                    client_info['last_activity'] = time.time()
                    self.stats['messages_received'] += 1
                    self.stats['last_activity'] = time.time()
                    
                    # Process message based on client type and message type
                    if client_type == 'sensor':
                        await self._handle_sensor_message(websocket, data)
                    elif client_type == 'memory':
                        await self._handle_memory_message(websocket, data)
                    elif client_type == 'llm':
                        await self._handle_llm_message(websocket, data)
                    elif client_type == 'ui':
                        await self._handle_ui_message(websocket, data)
                    elif client_type == 'application':
                        await self._handle_application_message(websocket, data)
                    else:
                        # Generic handlers for other client types
                        if message_type == 'ping':
                            try:
                                await websocket.send(json.dumps({
                                    'type': 'pong',
                                    'timestamp': time.time()
                                }))
                            except:
                                logger.debug("Error sending pong, websocket may be closed")
                        elif message_type == 'status':
                            await self._send_status(websocket)
                        else:
                            logger.debug(f"Unhandled message type '{message_type}' from {client_type} client")
                
                except json.JSONDecodeError:
                    try:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON message'
                        }))
                    except:
                        logger.debug("Error sending JSON error, websocket may be closed")
                    self.stats['errors'] += 1
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    self.stats['errors'] += 1
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"{client_type} client disconnected: {client_info['ip']} - {e.code} {e.reason}")
        except Exception as e:
            logger.error(f"Error in connection handler: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Remove client from appropriate set
            if client_type in self.clients and websocket in self.clients[client_type]:
                self.clients[client_type].remove(websocket)
            
            # Remove client state
            if websocket in self.client_states:
                del self.client_states[websocket]
            
            # Log disconnection
            logger.info(f"{client_type} client from {client_info['ip']} disconnected after "
                      f"{client_info['messages_received']} messages")
    
    async def _handle_sensor_message(self, websocket, data):
        """Handle messages from sensor clients"""
        message_type = data.get('type', '')
        
        if message_type == 'sensor_data':
            # Extract sensor data
            sensor_type = data.get('sensor_type', '')
            payload = data.get('data', {})
            
            if not sensor_type or not payload:
                try:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid sensor data: missing sensor_type or data'
                    }))
                except:
                    logger.debug("Error sending error message, websocket may be closed")
                return
            
            # Add timestamp if not present
            if 'timestamp' not in payload:
                payload['timestamp'] = time.time()
            
            # Buffer the data
            if sensor_type in self.sensor_data_buffers:
                # Add to buffer (at beginning for newest-first order)
                self.sensor_data_buffers[sensor_type].insert(0, payload)
                
                # Trim buffer if needed
                if len(self.sensor_data_buffers[sensor_type]) > self.max_buffer_size:
                    self.sensor_data_buffers[sensor_type] = self.sensor_data_buffers[sensor_type][:self.max_buffer_size]
            
            # Log sensor data received
            logger.debug(f"Received {sensor_type} sensor data: {payload.get('image_hash', '')} at {payload.get('timestamp', '')}")
            
            # Route to memory clients immediately with priority
            broadcast_message = {
                'type': 'sensor_data',
                'sensor_type': sensor_type,
                'data': payload,
                'timestamp': payload.get('timestamp', time.time())
            }
            
            await self.broadcast_to_memory_clients(broadcast_message)
            
            # Send acknowledgment
            try:
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message_type': message_type,
                    'status': 'success',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending ack message, websocket may be closed")
        
        elif message_type == 'ping':
            try:
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending pong message, websocket may be closed")
        
        elif message_type == 'status':
            await self._send_status(websocket)
        
        else:
            logger.warning(f"Unhandled sensor message type: {message_type}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unhandled message type: {message_type}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _handle_memory_message(self, websocket, data):
        """Handle messages from memory system clients"""
        message_type = data.get('type', '')
        
        if message_type == 'memory_request':
            # Handle request for historical sensor data
            sensor_type = data.get('sensor_type', '')
            count = data.get('count', 1)
            
            if sensor_type in self.sensor_data_buffers:
                # Get requested number of items (or all available)
                items = self.sensor_data_buffers[sensor_type][:count] if count > 0 else self.sensor_data_buffers[sensor_type]
                
                # Send response
                try:
                    await websocket.send(json.dumps({
                        'type': 'memory_response',
                        'sensor_type': sensor_type,
                        'data': items,
                        'count': len(items),
                        'timestamp': time.time()
                    }))
                except:
                    logger.debug("Error sending memory response, websocket may be closed")
            else:
                try:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Invalid sensor type: {sensor_type}'
                    }))
                except:
                    logger.debug("Error sending error message, websocket may be closed")
        
        elif message_type == 'ping':
            try:
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending pong message, websocket may be closed")
        
        elif message_type == 'status':
            await self._send_status(websocket)
        
        else:
            logger.warning(f"Unhandled memory message type: {message_type}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unhandled message type: {message_type}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _handle_llm_message(self, websocket, data):
        """Handle messages from LLM service clients"""
        message_type = data.get('type', '')
        
        if message_type == 'llm_response':
            # LLM has generated a response - route to appropriate clients
            response_data = data.get('data', {})
            destination = data.get('destination', 'ui')
            
            if destination == 'ui':
                # Broadcast to UI clients
                await self.broadcast_to_ui_clients({
                    'type': 'llm_response',
                    'data': response_data,
                    'timestamp': time.time()
                })
            elif destination == 'memory':
                # Send to memory clients
                await self.broadcast_to_memory_clients({
                    'type': 'llm_response',
                    'data': response_data,
                    'timestamp': time.time()
                })
            elif destination == 'application':
                # Send to application clients
                await self.broadcast_to_application_clients({
                    'type': 'llm_response',
                    'data': response_data,
                    'timestamp': time.time()
                })
            else:
                logger.warning(f"Invalid LLM response destination: {destination}")
            
            # Send acknowledgment
            try:
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message_type': message_type,
                    'status': 'success',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending ack message, websocket may be closed")
        
        elif message_type == 'ping':
            try:
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending pong message, websocket may be closed")
        
        elif message_type == 'status':
            await self._send_status(websocket)
        
        else:
            logger.warning(f"Unhandled LLM message type: {message_type}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unhandled message type: {message_type}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _handle_ui_message(self, websocket, data):
        """Handle messages from UI/overlay clients"""
        message_type = data.get('type', '')
        
        if message_type == 'request_context':
            # UI is requesting context information
            await self._send_context_to_ui(websocket)
        
        elif message_type == 'user_message' or message_type == 'llm_request':
            # User message from UI - route to LLM service
            message = data.get('message', '') or data.get('payload', {}).get('query', '')
            if message:
                await self.broadcast_to_llm_clients({
                    'type': 'user_message',
                    'message': message,
                    'timestamp': time.time()
                })
                
                # Send acknowledgment
                try:
                    await websocket.send(json.dumps({
                        'type': 'ack',
                        'message_type': message_type,
                        'status': 'success',
                        'timestamp': time.time()
                    }))
                except:
                    logger.debug("Error sending ack message, websocket may be closed")
            else:
                try:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Empty user message'
                    }))
                except:
                    logger.debug("Error sending error message, websocket may be closed")
        
        elif message_type == 'ping':
            try:
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending pong message, websocket may be closed")
        
        elif message_type == 'status':
            await self._send_status(websocket)
        
        else:
            logger.warning(f"Unhandled UI message type: {message_type}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unhandled message type: {message_type}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _handle_application_message(self, websocket, data):
        """Handle messages from application clients"""
        message_type = data.get('type', '')
        
        if message_type == 'application_event':
            # Application event - route to memory clients
            event_data = data.get('data', {})
            
            await self.broadcast_to_memory_clients({
                'type': 'application_event',
                'data': event_data,
                'timestamp': time.time()
            })
            
            # Send acknowledgment
            try:
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message_type': message_type,
                    'status': 'success',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending ack message, websocket may be closed")
        
        elif message_type == 'ping':
            try:
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending pong message, websocket may be closed")
        
        elif message_type == 'status':
            await self._send_status(websocket)
        
        else:
            logger.warning(f"Unhandled application message type: {message_type}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unhandled message type: {message_type}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _send_context_to_ui(self, websocket):
        """Send context information to a UI client"""
        try:
            # Get the most recent sensor data
            context = {
                'screen': self.sensor_data_buffers.get('screen', [])[0] if self.sensor_data_buffers.get('screen') else {},
                'process': self.sensor_data_buffers.get('process', [])[0] if self.sensor_data_buffers.get('process') else {},
                'server_stats': self.stats,
                'timestamp': time.time()
            }
            
            # Send context
            try:
                await websocket.send(json.dumps({
                    'type': 'context_update',
                    'data': context,
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending context update, websocket may be closed")
            
        except Exception as e:
            logger.error(f"Error sending context to UI: {e}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Error getting context: {str(e)}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def _send_status(self, websocket):
        """Send server status information to a client"""
        try:
            # Prepare status information
            status = {
                'server_time': datetime.now().isoformat(),
                'uptime': time.time() - self.stats['start_time'],
                'clients': {
                    client_type: len(clients) for client_type, clients in self.clients.items()
                },
                'stats': self.stats,
                'buffer_sizes': {
                    sensor_type: len(buffer) for sensor_type, buffer in self.sensor_data_buffers.items()
                }
            }
            
            # Send status
            try:
                await websocket.send(json.dumps({
                    'type': 'status_response',
                    'status': status,
                    'timestamp': time.time()
                }))
            except:
                logger.debug("Error sending status response, websocket may be closed")
            
        except Exception as e:
            logger.error(f"Error sending status: {e}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Error getting status: {str(e)}'
                }))
            except:
                logger.debug("Error sending error message, websocket may be closed")
    
    async def broadcast_to_memory_clients(self, message):
        """Broadcast message to all memory system clients"""
        try:
            if not self.clients['memory']:
                logger.warning("No memory clients connected to receive message")
                return
            
            msg_str = json.dumps(message)
            
            # Track successes and failures
            sent_count = 0
            error_count = 0
            closed_clients = set()
            
            # Send to all memory clients
            for ws in self.clients['memory'].copy():
                try:
                    await ws.send(msg_str)
                    sent_count += 1
                    self.stats['messages_sent'] += 1
                except websockets.exceptions.ConnectionClosed:
                    closed_clients.add(ws)
                    error_count += 1
                except Exception as e:
                    logger.error(f"Error sending to memory client: {e}")
                    error_count += 1
            
            # Remove closed clients
            for ws in closed_clients:
                self.clients['memory'].discard(ws)
                if ws in self.client_states:
                    del self.client_states[ws]
            
            if error_count > 0:
                logger.warning(f"Errors sending to {error_count}/{sent_count + error_count} memory clients")
            
            logger.debug(f"Broadcast to {sent_count} memory clients successful")
            
        except Exception as e:
            logger.error(f"Error broadcasting to memory clients: {e}")
    
    async def broadcast_to_llm_clients(self, message):
        """Broadcast message to all LLM service clients"""
        try:
            if not self.clients['llm']:
                logger.warning("No LLM clients connected to receive message")
                return
            
            msg_str = json.dumps(message)
            
            # Send to all LLM clients
            for ws in self.clients['llm'].copy():
                try:
                    await ws.send(msg_str)
                    self.stats['messages_sent'] += 1
                except websockets.exceptions.ConnectionClosed:
                    logger.debug("LLM client connection closed, removing from clients")
                    self.clients['llm'].discard(ws)
                except Exception as e:
                    logger.error(f"Error sending to LLM client: {e}")
            
            logger.debug(f"Broadcast to {len(self.clients['llm'])} LLM clients successful")
            
        except Exception as e:
            logger.error(f"Error broadcasting to LLM clients: {e}")
    
    async def broadcast_to_ui_clients(self, message):
        """Broadcast message to all UI/overlay clients"""
        try:
            if not self.clients['ui']:
                logger.warning("No UI clients connected to receive message")
                return
            
            msg_str = json.dumps(message)
            
            # Send to all UI clients
            for ws in self.clients['ui'].copy():
                try:
                    await ws.send(msg_str)
                    self.stats['messages_sent'] += 1
                except websockets.exceptions.ConnectionClosed:
                    logger.debug("UI client connection closed, removing from clients")
                    self.clients['ui'].discard(ws)
                except Exception as e:
                    logger.error(f"Error sending to UI client: {e}")
            
            logger.debug(f"Broadcast to {len(self.clients['ui'])} UI clients successful")
            
        except Exception as e:
            logger.error(f"Error broadcasting to UI clients: {e}")
    
    async def broadcast_to_application_clients(self, message):
        """Broadcast message to all application clients"""
        try:
            if not self.clients['application']:
                logger.warning("No application clients connected to receive message")
                return
            
            msg_str = json.dumps(message)
            
            # Send to all application clients
            for ws in self.clients['application'].copy():
                try:
                    await ws.send(msg_str)
                    self.stats['messages_sent'] += 1
                except websockets.exceptions.ConnectionClosed:
                    logger.debug("Application client connection closed, removing from clients")
                    self.clients['application'].discard(ws)
                except Exception as e:
                    logger.error(f"Error sending to application client: {e}")
            
            logger.debug(f"Broadcast to {len(self.clients['application'])} application clients successful")
            
        except Exception as e:
            logger.error(f"Error broadcasting to application clients: {e}")
    
    async def _periodic_tasks(self):
        """Run periodic maintenance tasks"""
        try:
            while not self.stopping:
                # Log statistics every minute
                if int(time.time()) % 60 == 0:
                    total_clients = sum(len(clients) for clients in self.clients.values())
                    logger.info(f"Bridge server stats: {total_clients} clients, "
                              f"msgs received: {self.stats['messages_received']}, "
                              f"msgs sent: {self.stats['messages_sent']}, "
                              f"errors: {self.stats['errors']}")
                
                # Check for stale clients and clean up
                await self._cleanup_stale_clients()
                
                # Sleep for a bit
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Periodic tasks cancelled")
        except Exception as e:
            logger.error(f"Error in periodic tasks: {e}")
            logger.error(traceback.format_exc())
    
    async def _cleanup_stale_clients(self):
        """Remove clients that haven't sent messages in a while"""
        try:
            current_time = time.time()
            timeout = 300  # 5 minutes
            
            # Check each client type
            for client_type, clients in self.clients.items():
                stale_clients = set()
                
                # Identify stale clients
                for ws in clients:
                    client_info = self.client_states.get(ws)
                    if not client_info:
                        continue
                    
                    # Check if client is stale
                    if current_time - client_info['last_activity'] > timeout:
                        stale_clients.add(ws)
                
                # Remove stale clients
                if stale_clients:
                    logger.info(f"Removing {len(stale_clients)} stale {client_type} clients")
                    for ws in stale_clients:
                        try:
                            await ws.close(1000, "Connection timed out due to inactivity")
                            clients.discard(ws)
                            if ws in self.client_states:
                                del self.client_states[ws]
                        except Exception as e:
                            logger.warning(f"Error closing stale {client_type} client: {e}")
                            clients.discard(ws)
                            if ws in self.client_states:
                                del self.client_states[ws]
            
        except Exception as e:
            logger.error(f"Error cleaning up stale clients: {e}")

async def main():
    """Main function to run the bridge server."""
    try:
        # Create the bridge server
        bridge_server = EnhancedBridgeServer()
        
        # Start the server
        await bridge_server.start()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up if needed
        try:
            await bridge_server.stop()
        except:
            pass

if __name__ == "__main__":
    try:
        # Create pids directory if it doesn't exist
        os.makedirs("pids", exist_ok=True)
        
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bridge server stopped by keyboard interrupt")
        try:
            # Remove PID file
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except:
            pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())