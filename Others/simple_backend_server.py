#!/usr/bin/env python3
"""
Simple Backend Server for WebSocket Communication
- Frontend communicates with this server on port 8765
- No external dependencies required
- Provides local mock responses but in the format expected by the frontend
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import socket
import random
import traceback
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_backend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
context_data = {}
message_history = []

async def generate_mock_response(query, context=None):
    """Generate a mock response to a user query."""
    try:
        logger.info(f"Generating response for query: {query}")
        
        # Store the user query
        message_history.append({
            "type": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Predefined response templates
        response_templates = [
            "I understand you're asking about '{query}'. Here's what I can help with: {detail}",
            "Thanks for your query about '{query}'. {detail}",
            "I've analyzed your request about '{query}'. {detail}",
            "Regarding '{query}', I can provide the following information: {detail}"
        ]
        
        personalized_responses = {
            "what can you help me with": [
                "I can help you with analyzing your environment, monitoring system activity, answering questions about your work, and providing personalized assistance based on what you're doing.",
                "I'm designed to assist with a variety of tasks including analyzing your screen content, monitoring running applications, answering questions, and providing contextual assistance.",
                "I can assist you by monitoring your work environment, providing relevant information based on your context, answering questions, and helping with productivity tasks."
            ],
            "how does this work": [
                "This system monitors your environment through sensors that track your screen content and running applications. It then uses this context to provide more relevant assistance.",
                "The system uses various sensors to understand your work context, including what's on your screen and which applications you're using. This helps me provide more personalized responses.",
                "I work by collecting contextual information about your activities, which helps me understand what you're working on and provide more relevant assistance."
            ],
            "now": [
                "I'm ready to assist you with your current tasks. What specifically would you like help with?",
                "Now that the system is running, I can provide assistance based on your current work context. How can I help?",
                "I'm actively monitoring your work environment and ready to provide assistance. What would you like to know?"
            ],
            "hey": [
                "Hello! I'm here to assist you. What can I help with today?",
                "Hi there! I'm ready to help with your questions or tasks.",
                "Greetings! How can I assist you with your current activities?"
            ],
            "time": [
                f"The current time is {datetime.now().strftime('%H:%M:%S')}.",
                f"It's currently {datetime.now().strftime('%I:%M %p')}.",
                f"The time is {datetime.now().strftime('%H:%M')}"
            ],
            "help": [
                "You can ask me about your current applications, request information, or ask for assistance with tasks. I'll do my best to provide helpful responses.",
                "I can help with various tasks. Just ask a question, and I'll respond based on the available information.",
                "Feel free to ask me anything, and I'll provide the best response I can based on your query."
            ],
        }
        
        # Find most appropriate response
        query_lower = query.lower()
        response_detail = "I can provide information and assistance based on your current context."
        
        # Check if we have a personalized response
        for key, responses in personalized_responses.items():
            if key in query_lower:
                response_detail = random.choice(responses)
                break
        
        # Add context information if available
        if context:
            active_window = context.get('active_window', 'Unknown')
            response_detail += f" I notice you're currently using {active_window}."
        
        # Format the response
        template = random.choice(response_templates)
        response = template.format(query=query, detail=response_detail)
        
        # Store the assistant response
        message_history.append({
            "type": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add a short delay to simulate processing
        await asyncio.sleep(0.5)
        
        return {
            "type": "query_response",
            "payload": {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        logger.error(traceback.format_exc())
        return {
            "type": "query_response",
            "payload": {
                "query": query,
                "response": "I'm sorry, I encountered an error processing your request.",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }

async def process_user_interaction(message_data, websocket):
    """Process a user interaction message"""
    global context_data
    
    payload = message_data.get('payload', {})
    
    if payload.get('type') == 'query':
        query = payload.get('query', '')
        logger.info(f"Processing query: {query}")
        
        # Generate a response using context_data
        response_data = await generate_mock_response(query, context_data)
        
        # Send back to the client
        await websocket.send(json.dumps(response_data))
        logger.info(f"Sent response for query: {query}")
    elif payload.get('type') == 'sensor_data':
        # If we have sensor data, store it
        logger.info(f"Received sensor data of type: {payload.get('sensor_type', 'unknown')}")
        
        sensor_type = payload.get('sensor_type')
        sensor_data = payload.get('data', {})
        
        # Update context data
        if sensor_type:
            context_data[sensor_type] = sensor_data
        
        # Acknowledge receipt
        await websocket.send(json.dumps({
            "type": "sensor_data_received",
            "payload": {
                "sensor_type": sensor_type,
                "timestamp": datetime.now().isoformat()
            }
        }))
    else:
        # Echo back with timestamp for other interaction types
        await websocket.send(json.dumps({
            "type": "echo",
            "data": message_data,
            "timestamp": datetime.now().isoformat()
        }))

async def handler(websocket):
    """Handle WebSocket connections."""
    global context_data
    
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message with information about available systems
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to simple backend server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown_type')
                logger.info(f"Received message from client {client_id}: {msg_type}")
                
                # Process different message types
                if data.get('type') == 'user_interaction':
                    await process_user_interaction(data, websocket)
                elif data.get('type') == 'context_update':
                    # Update our context data
                    new_context = data.get('payload', {})
                    context_data.update(new_context)
                    logger.info("Context data updated")
                    
                    # Acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "context_update_received",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif data.get('type') == 'sensor_data':
                    # Process sensor data
                    sensor_payload = data.get('payload', {})
                    sensor_type = sensor_payload.get('sensor_type', 'unknown')
                    sensor_data = sensor_payload.get('data', {})
                    
                    # Update context data
                    if sensor_type:
                        context_data[sensor_type] = sensor_data
                    
                    # Acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "sensor_data_received",
                        "payload": {
                            "sensor_type": sensor_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                elif data.get('type') == 'status_request':
                    # Send status information
                    status_data = {
                        "connected_clients": len(connected_clients),
                        "context_data_size": len(str(context_data)),
                        "message_history_count": len(message_history),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps({
                        "type": "status_response",
                        "payload": status_data
                    }))
                    logger.info("Sent status information")
                else:
                    # Echo back with timestamp for other message types
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                logger.error(traceback.format_exc())
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Error processing message: {str(e)}"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    global context_data
    
    while True:
        if connected_clients:
            # Create status message
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "context_data_size": len(str(context_data)),
                    "message_history_count": len(message_history),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(10)

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

async def main():
    """Main function to start the WebSocket server."""
    try:
        global context_data
        
        # Use port 8765 to match the Tauri app's expectation
        port = 8765
        
        # Check if port is in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            
            # Try to forcefully release the port by killing any process using it
            os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
            os.system(f"pkill -f 'port {port}' 2>/dev/null || true")
            
            # Wait a moment for the port to be released
            await asyncio.sleep(1)
            
            # Check again
            if is_port_in_use(port):
                logger.error("Failed to release port")
                sys.exit(1)
                
        # Create the server
        server = await websockets.serve(
            handler,
            "0.0.0.0",  # Bind to all interfaces
            port,
            ping_interval=10,
            ping_timeout=5
        )
        
        logger.info(f"Simple backend server started on ws://0.0.0.0:{port}")
        
        # Save PID to file
        os.makedirs('pids', exist_ok=True)
        with open('pids/simple_backend_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)