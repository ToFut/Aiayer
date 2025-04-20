#!/usr/bin/env python3
"""
WebSocket Server - Standalone WebSocket server for backend communication

This module provides a standalone WebSocket server that the bridge and overlay
can connect to. It serves as the backend communication endpoint.
"""

import sys
import asyncio
import websockets
import logging
import signal
import json
import time
import argparse
import os
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/websocket.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("websocket_server")

# Global state
clients = set()
message_history = []

async def handle_connection(websocket):
    """Handle a WebSocket connection."""
    global clients, message_history
    
    # Add client to set
    clients.add(websocket)
    logger.info(f"New client connected. Total clients: {len(clients)}")
    
    # Send initial status
    await websocket.send(json.dumps({
        'type': 'connection_status',
        'payload': {
            'status': 'connected',
            'server_time': datetime.now().isoformat(),
            'message': 'Welcome to the Local Assistant WebSocket Server'
        }
    }))
    
    # CRITICAL FIX: Send an immediate completion status to clear any stuck UI state
    # This ensures that any previously stuck 'processing' state is immediately cleared
    await websocket.send(json.dumps({
        'type': 'query_status',
        'payload': {
            'status': 'complete',
            'transaction_id': f"init_{int(time.time())}",
            'message': 'Client connection initialized, clearing any previous states',
            'timestamp': datetime.now().isoformat()
        }
    }))
    
    # Send recent message history
    if message_history:
        await websocket.send(json.dumps({
            'type': 'message_history',
            'payload': message_history[-10:]  # Send last 10 messages
        }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type')
                payload = data.get('payload', {})
                
                logger.info(f"Received message of type: {message_type}")
                
                if message_type == 'heartbeat':
                    # Respond to heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'payload': {
                            'server_time': datetime.now().isoformat(),
                            'status': 'ok',
                            'backend_connected': True
                        }
                    }))
                    
                # CRITICAL FIX: Handler for emergency UI fix messages
                elif message_type in ['emergency_abort', 'clear_messages', 'inject_script']:
                    # Process emergency messages
                    emergency_id = payload.get('transaction_id', f"emergency_{int(time.time())}")
                    logger.warning(f"Received emergency message type {message_type} with ID {emergency_id}")
                    
                    # Forward the emergency message to all clients
                    await broadcast_message(message_type, payload)
                    
                    # For emergency abort or clear_messages, also send completion status
                    if message_type in ['emergency_abort', 'clear_messages']:
                        # Send a completion status to ensure UI clears any processing state
                        await broadcast_message('query_status', {
                            'status': 'complete',
                            'transaction_id': emergency_id,
                            'message': 'Emergency completion triggered',
                            'timestamp': datetime.now().isoformat(),
                            'emergency': True
                        })
                        logger.info(f"Sent emergency completion status for {message_type}")
                        
                        # Clear any in-progress queries
                        in_progress_query_count = len(in_progress_queries)
                        in_progress_queries.clear()
                        logger.info(f"Cleared {in_progress_query_count} in-progress queries")
                
                elif message_type == 'connection_established':
                    # Acknowledge connection
                    logger.info(f"Client identified: {payload.get('client', 'unknown')}, version: {payload.get('version', 'unknown')}")
                    await websocket.send(json.dumps({
                        'type': 'connection_status',
                        'payload': {
                            'status': 'connected',
                            'server_time': datetime.now().isoformat(),
                            'client': payload.get('client'),
                            'version': payload.get('version')
                        }
                    }))
                
                elif message_type == 'request_sensor_data':
                    # Handle sensor data request
                    logger.info("Received sensor data request")
                    await handle_sensor_data_request(payload)
                
                elif message_type == 'request_context':
                    # Handle context request
                    logger.info("Received context request")
                    await handle_context_request(payload)
                
                elif message_type == 'chat_message':
                    # Store in history
                    history_item = {
                        'type': 'chat_message',
                        'time': datetime.now().isoformat(),
                        'payload': payload,
                        'direction': 'received'
                    }
                    message_history.append(history_item)
                    
                    # Extract message text
                    message_text = payload.get('text', '')
                    logger.info(f"Received direct chat message: {message_text}")
                    
                    # Broadcast to all clients
                    await broadcast_message('chat_message', payload)
                    
                    # Relay message to main app without auto-response
                    logger.info(f"Relaying chat message to main app: '{message_text}'")
                
                elif message_type == 'user_interaction':
                    # Handle user interaction
                    logger.info(f"Processing user interaction: {payload}")
                    
                    # Handle chat message format from overlay
                    if payload.get('type') == 'chat_message' and 'text' in payload.get('data', {}):
                        text = payload['data']['text']
                        logger.info(f"Received chat message via user_interaction: {text}")
                        
                        # Store in history
                        history_item = {
                            'type': 'user_interaction',
                            'time': datetime.now().isoformat(),
                            'payload': payload,
                            'direction': 'received'
                        }
                        message_history.append(history_item)
                        
                        # Relay user interaction to main app by broadcasting
                        logger.info(f"Relaying user interaction chat message to main app: '{text}'")
                        await broadcast_message('user_interaction', payload)
                        
                        # Also send immediate thinking indicator
                        await broadcast_message('query_status', {
                            'status': 'processing',
                            'query': text,
                            'message': 'Processing your request...'
                        })
                        
                        # Set up a timeout task to notify if processing takes too long (reduced from 30 to 15 seconds)
                        asyncio.create_task(handle_response_timeout(text, 15))
                    
                    # Handle query format from overlay
                    elif payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"Received query via user_interaction: {query}")
                        
                        # Store in history
                        history_item = {
                            'type': 'user_interaction',
                            'time': datetime.now().isoformat(),
                            'payload': payload,
                            'direction': 'received'
                        }
                        message_history.append(history_item)
                        
                        # Relay query to main app by broadcasting
                        logger.info(f"Relaying query to main app: '{query}'")
                        await broadcast_message('user_interaction', payload)
                        
                        # Send immediate thinking indicator
                        await broadcast_message('query_status', {
                            'status': 'processing',
                            'query': query,
                            'message': 'Processing your request...'
                        })
                        
                        # Set up a timeout task to notify if processing takes too long (reduced from 30 to 15 seconds)
                        asyncio.create_task(handle_response_timeout(query, 15))
                
                else:
                    # Echo other messages
                    logger.info(f"Received unhandled message type: {message_type}")
                    await websocket.send(json.dumps({
                        'type': 'echo',
                        'payload': payload
                    }))
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON message")
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed: {e.code} - {e.reason}")
    except Exception as e:
        logger.error(f"Error in connection handler: {e}")
    finally:
        clients.remove(websocket)
        logger.info(f"Client disconnected. Remaining clients: {len(clients)}")

async def handle_sensor_data_request(payload):
    """Handle sensor data requests from clients."""
    try:
        # Get sensor data from the main application
        sensor_data = {
            'type': 'sensor_data',
            'data': {
                'screen': {
                    'text': 'Sample screen text',
                    'has_images': False,
                    'has_videos': False
                },
                'process': {
                    'active_app': 'Sample App',
                    'window_title': 'Sample Window'
                },
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Broadcast sensor data to all clients
        await broadcast_message('sensor_data', sensor_data)
        
    except Exception as e:
        logger.error(f"Error handling sensor data request: {e}")
        await broadcast_message('error', {
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

async def handle_context_request(payload):
    """Handle context requests from clients."""
    try:
        # Get context data from the main application
        context_data = {
            'type': 'context_update',
            'data': {
                'screen_context': 'Sample screen context',
                'process_context': 'Sample process context',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Broadcast context data to all clients
        await broadcast_message('context_update', context_data)
        
    except Exception as e:
        logger.error(f"Error handling context request: {e}")
        await broadcast_message('error', {
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Query tracking
in_progress_queries = {}

async def handle_response_timeout(query, timeout_seconds):
    """Handle timeout for a query response with progressive fallbacks and guaranteed completion."""
    query_id = f"query_{int(time.time())}_{hash(query) % 10000}"  # More unique ID to avoid collisions
    in_progress_queries[query_id] = query
    
    # Log that we're tracking this query
    logger.info(f"[TRANSACTION:{query_id}] Started tracking query: '{query[:30]}...'")
    
    try:
        # CRITICAL FIX: Multiple independent watchdogs at different time intervals
        # This ensures we have multiple chances to detect and fix stuck messages
        
        # Primary watchdog - guaranteed completion after absolute timeout (10 seconds)
        async def primary_watchdog():
            # Primary watchdog kicks in quickly at 10 seconds (reduced from 20)
            await asyncio.sleep(10)
            
            # Check if query is still marked as in-progress
            if query_id in in_progress_queries:
                logger.warning(f"[TRANSACTION:{query_id}] PRIMARY WATCHDOG: Forcing completion after 10s timeout: '{query[:30]}...'")
                
                # Force a complete status to be sent
                await broadcast_message('query_status', {
                    'status': 'complete',
                    'query': query,
                    'transaction_id': f"{query_id}_watchdog1",
                    'has_error': True,
                    'is_watchdog': True,
                    'message': 'The request has been completed by the primary watchdog timer.'
                })
                
                # Send a clear message that processing has stopped
                await broadcast_message('chat_response', {
                    'text': "I've reset the system as the response was taking too long. Please try asking again.",
                    'timestamp': datetime.now().isoformat(),
                    'transaction_id': f"{query_id}_watchdog1",
                    'is_watchdog': True,
                    'is_fallback': True
                })
                
                # Mark query as completed
                if query_id in in_progress_queries:
                    in_progress_queries.pop(query_id, None)
                    logger.info(f"[TRANSACTION:{query_id}] PRIMARY WATCHDOG: Successfully removed query from tracking")
        
        # Secondary watchdog - absolute guarantee after 20 seconds
        async def secondary_watchdog():
            # Secondary watchdog kicks in at 20 seconds as a backup
            await asyncio.sleep(20)
            
            # Check if query is somehow still in progress despite the primary watchdog
            if query_id in in_progress_queries:
                logger.error(f"[TRANSACTION:{query_id}] SECONDARY WATCHDOG: Query still in progress after 20s! Forcing completion: '{query[:30]}...'")
                
                # Force a complete status with emergency flag
                await broadcast_message('query_status', {
                    'status': 'complete',
                    'query': query,
                    'transaction_id': f"{query_id}_watchdog2",
                    'has_error': True,
                    'is_emergency': True,
                    'message': 'EMERGENCY: The request has been completed by the secondary watchdog timer.'
                })
                
                # Also inject a script to directly reset the UI state
                # This is our most aggressive recovery mechanism
                await broadcast_message('inject_script', {
                    'script': """
                        // Force reset UI state
                        console.log('EMERGENCY WATCHDOG: Clearing UI state');
                        if (typeof isThinking !== 'undefined') {
                            isThinking = false;
                        }
                        if (typeof messages !== 'undefined') {
                            // Remove any processing or typing messages
                            messages = messages.filter(m => {
                                if (m.isTyping) return false;
                                if (m.content && typeof m.content === 'string') {
                                    return !m.content.toLowerCase().includes('processing') && 
                                           !m.content.toLowerCase().includes('working on');
                                }
                                return true;
                            });
                            
                            // Add recovery message
                            messages.push({
                                type: 'assistant',
                                content: 'The system has been reset due to a timeout. Please try again.',
                                isSystemGenerated: true,
                                isError: true,
                                timestamp: Date.now()
                            });
                            
                            // Try to scroll to bottom
                            if (typeof scrollToBottom === 'function') {
                                scrollToBottom();
                            }
                        }
                    """,
                    'transaction_id': f"{query_id}_watchdog2",
                    'emergency': True
                })
                
                # Clear ALL in-progress queries to reset the system
                in_progress_queries.clear()
                logger.info(f"[TRANSACTION:{query_id}] SECONDARY WATCHDOG: Cleared all in-progress queries")
        
        # Start BOTH watchdogs independently
        # This ensures we have multiple chances to recover from a stuck state
        asyncio.create_task(primary_watchdog())
        asyncio.create_task(secondary_watchdog())
        
        # NORMAL FLOW: Progressive response with multiple phases
        
        # First phase: Initial waiting period (very short - 3 seconds)
        initial_wait = min(3, timeout_seconds * 0.3)  # Maximum 3 seconds for first phase (reduced from 5)
        await asyncio.sleep(initial_wait)
        
        # First check: Is the query still in progress?
        if query_id in in_progress_queries:
            logger.info(f"[TRANSACTION:{query_id}] Phase 1: Query taking longer than expected ({initial_wait:.1f}s)")
            
            # Send initial "working on it" status
            await broadcast_message('query_status', {
                'status': 'processing',
                'query': query,
                'transaction_id': f"{query_id}_phase1",
                'message': 'Working on your request, just a moment more...'
            })
            
            # Second phase: Short additional wait
            second_wait = min(3, timeout_seconds * 0.2)  # Maximum 3 seconds for second phase (reduced from 5)
            await asyncio.sleep(second_wait)
            
            # Second check: Still in progress?
            if query_id in in_progress_queries:
                logger.info(f"[TRANSACTION:{query_id}] Phase 2: Query delayed ({initial_wait + second_wait:.1f}s)")
                
                # Immediately send a partial response to show progress
                # This is critical to show the UI is responsive
                partial_message = ""
                if len(query) < 15:
                    partial_message = f"I'm working on your request about '{query}'. One moment please..."
                elif any(kw in query.lower() for kw in ["help", "how to", "how do"]):
                    partial_message = "I'm gathering information to help with your question. This might take a moment..."
                elif any(kw in query.lower() for kw in ["error", "issue", "problem", "fix"]):
                    partial_message = "I'm analyzing your issue to find the best solution. Just a moment more..."
                else:
                    partial_message = "I'm processing your request and will have a response for you very soon..."
                
                # Send this partial message as a chat response
                await broadcast_message('chat_response', {
                    'text': partial_message,
                    'timestamp': datetime.now().isoformat(),
                    'transaction_id': f"{query_id}_partial",
                    'is_partial': True  # Flag this as a partial response
                })
                
                # Register this partial response for automatic clearing
                # This ensures any "I'm processing" messages get cleared automatically
                asyncio.create_task(self_clear_processing_message(query_id, partial_message, 7))  # Clear after 7 seconds
                
                # Final phase: Very short final wait
                final_wait = min(2, timeout_seconds * 0.1)  # Maximum 2 seconds for final phase (reduced from 5)
                await asyncio.sleep(final_wait)
                
                # Final check: Still no response?
                if query_id in in_progress_queries:
                    logger.warning(f"[TRANSACTION:{query_id}] Phase 3: Query timeout ({initial_wait + second_wait + final_wait:.1f}s)")
                    
                    # Provide a helpful fallback that's specific to the query
                    fallback_message = ""
                    
                    # Tailor the fallback message based on query content
                    if "help" in query.lower():
                        fallback_message = "I'd like to help you with this. Could you please break your question down into smaller parts? This will help me respond more effectively."
                    elif any(kw in query.lower() for kw in ["error", "problem", "bug", "fix", "issue"]):
                        fallback_message = "I understand you're experiencing an issue. To help troubleshoot, could you please describe the specific problem again in a bit more detail?"
                    elif len(query) > 200:
                        fallback_message = "Your question is quite detailed. To help you more effectively, could you ask a more focused question about a specific aspect of your inquiry?"
                    else:
                        fallback_message = "I wasn't able to complete processing your request in time. This could be due to high system load or complexity. Could you try asking a simpler or more specific question?"
                    
                    # Send the fallback response
                    await broadcast_message('chat_response', {
                        'text': fallback_message,
                        'timestamp': datetime.now().isoformat(),
                        'transaction_id': f"{query_id}_fallback",
                        'is_fallback': True
                    })
                    
                    # Always send a COMPLETE status to unstick the UI
                    await broadcast_message('query_status', {
                        'status': 'complete',
                        'query': query,
                        'transaction_id': f"{query_id}_complete",
                        'has_error': True,
                        'message': 'The request has been completed. You can continue with other questions.'
                    })
                    
                    # Remove from tracking
                    in_progress_queries.pop(query_id, None)
                    logger.info(f"[TRANSACTION:{query_id}] Query marked as completed by timeout handler")
        
    except Exception as e:
        logger.error(f"[TRANSACTION:{query_id}] Error in timeout handler: {e}")
        # Make sure to clean up even on error
        if query_id in in_progress_queries:
            in_progress_queries.pop(query_id, None)
            
        # Even on error, send a complete status to unstick the UI
        try:
            await broadcast_message('query_status', {
                'status': 'complete',
                'query': query,
                'transaction_id': f"{query_id}_error",
                'has_error': True,
                'message': 'The request has been completed with an error. You can continue with other questions.'
            })
        except Exception as e2:
            logger.error(f"[TRANSACTION:{query_id}] Failed to send error completion status: {e2}")

async def self_clear_processing_message(query_id, message_text, delay_seconds):
    """Automatically clear a processing message after a delay."""
    # Wait for the specified delay
    await asyncio.sleep(delay_seconds)
    
    # Check if the query is still in progress
    if query_id in in_progress_queries:
        logger.info(f"[TRANSACTION:{query_id}] Auto-clearing processing message after {delay_seconds}s")
        
        try:
            # Send a replacement message
            await broadcast_message('chat_response', {
                'text': "I've reset the system as the response was taking too long. Please try asking again.",
                'timestamp': datetime.now().isoformat(),
                'transaction_id': f"{query_id}_autoclear",
                'replaces_processing': True,
                'is_fallback': True
            })
            
            # Send a completion status
            await broadcast_message('query_status', {
                'status': 'complete',
                'query': in_progress_queries[query_id],
                'transaction_id': f"{query_id}_autoclear",
                'message': 'Auto-cleared processing message'
            })
            
            # Remove from tracking
            in_progress_queries.pop(query_id, None)
            logger.info(f"[TRANSACTION:{query_id}] Successfully auto-cleared processing message")
        except Exception as e:
            logger.error(f"[TRANSACTION:{query_id}] Error auto-clearing processing message: {e}")

def mark_query_completed(query):
    """Mark a query as completed to prevent timeout handlers from firing."""
    # Remove any matching queries
    to_remove = []
    for query_id, q in in_progress_queries.items():
        if q == query:
            to_remove.append(query_id)
    
    for query_id in to_remove:
        in_progress_queries.pop(query_id, None)
    
    if to_remove:
        logger.info(f"Marked query as completed: '{query}'")
        return True
    return False

async def broadcast_message(message_type, payload):
    """Broadcast a message to all connected clients."""
    if not clients:
        logger.info("No clients connected, message not sent")
        return
        
    # Add to history
    history_item = {
        'type': message_type,
        'time': datetime.now().isoformat(),
        'payload': payload,
        'direction': 'sent'
    }
    message_history.append(history_item)
    
    # Log important messages for debugging
    if message_type in ['chat_response', 'query_response', 'query_status']:
        logger.info(f"Broadcasting important message of type: {message_type}")
        logger.info(f"Payload: {payload}")
        
        # Mark queries as completed when a response is sent
        if message_type in ['chat_response', 'query_response']:
            # Find the query text in the payload
            if isinstance(payload, dict):
                if 'query' in payload:
                    mark_query_completed(payload['query'])
                elif 'text' in payload and not payload.get('is_fallback', False):
                    # This is a successful response, mark any pending queries as completed
                    # This is a simplification, but helps prevent duplicate responses
                    for query_id in list(in_progress_queries.keys()):
                        in_progress_queries.pop(query_id, None)
                    logger.info("Cleared all pending queries after successful response")
    
    # Prepare message
    message = json.dumps({
        'type': message_type,
        'payload': payload
    })
    
    # Send to all clients
    disconnect_clients = []
    successful_sends = 0
    for client in clients:
        try:
            await client.send(message)
            successful_sends += 1
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Client connection closed when trying to send {message_type}")
            disconnect_clients.append(client)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            disconnect_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnect_clients:
        if client in clients:
            clients.remove(client)
            
    # Log successful sends
    if message_type in ['chat_response', 'query_response', 'query_status']:
        logger.info(f"Successfully sent {message_type} to {successful_sends} clients")

async def main(port=8765, debug=False):
    """Main function to run the WebSocket server"""
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start WebSocket server
    server = await websockets.serve(
        handle_connection, 
        "localhost", 
        port,
        ping_interval=20,  # Send ping every 20 seconds
        ping_timeout=10,   # Wait 10 seconds for pong
        close_timeout=5    # Wait 5 seconds for clean close
    )
    
    logger.info(f"WebSocket server running on localhost:{port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Keep the main task running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Server task cancelled")
    finally:
        # Shut down the server
        server.close()
        await server.wait_closed()
        logger.info("Server shutdown complete")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="WebSocket server for the overlay bridge")
    parser.add_argument("--port", type=int, default=8765,
                      help="Port to listen on (default: 8765)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Print startup information
    print("\n" + "="*60)
    print(" WebSocket Server for Overlay Bridge")
    print(f" Port: {args.port}")
    print(f" Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    print("="*60 + "\n")
    
    # Run the server
    try:
        asyncio.run(main(args.port, args.debug))
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        logger.info("Server stopped")