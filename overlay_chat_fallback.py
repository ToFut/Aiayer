#!/usr/bin/env python3
"""
Overlay Chat Fallback System

This script serves as a direct interface to connect to the 
overlay chat system and ensure it receives responses even when
the backend LLM service is having issues.
"""
import asyncio
import websockets
import json
import logging
import sys
import time
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay_chat_fallback.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Sample fallback responses when LLM service is unavailable
FALLBACK_RESPONSES = [
    "I can help you with monitoring your screen content, tracking processes, and providing context-aware assistance. What would you like to know about?",
    "The system can analyze what's on your screen, monitor running applications, and provide relevant information based on your context. How can I assist you?",
    "I'm designed to help with context-aware tasks like analyzing your screen content, monitoring processes, and providing relevant information. What specific functionality would you like to see?",
    "This AI assistant can track your activities, understand your context, and provide relevant information. Would you like me to explain how the system works?",
    "I can demonstrate my capabilities by analyzing your screen content, monitoring your processes, and providing context-based assistance. What aspects would you like me to focus on?"
]

async def connect_to_ws_server(uri="ws://localhost:8765"):
    """Connect to the WebSocket server and handle messages."""
    try:
        logger.info(f"Connecting to WebSocket server at {uri}...")
        async with websockets.connect(uri, ping_interval=None, close_timeout=5) as websocket:
            logger.info(f"Successfully connected to {uri}")
            
            # Register as a client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "fallback_service",
                    "client_id": f"fallback_{int(time.time())}",
                    "version": "1.0.0"
                }
            }
            
            logger.info(f"Sending registration: {register_message}")
            await websocket.send(json.dumps(register_message))
            
            # Wait for connection response
            response = await websocket.recv()
            logger.info(f"Connection response: {response}")
            
            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    
                    logger.info(f"Received message type: {msg_type}")
                    
                    # Handle LLM request specifically
                    if msg_type == 'llm_request':
                        logger.info("Received LLM request, sending fallback response")
                        await handle_llm_request(websocket, data)
                    elif msg_type == 'status_update':
                        # Just log status updates
                        logger.info(f"Status update: {data.get('data', {}).get('client_count', 0)} clients connected")
                    else:
                        logger.info(f"Received other message type: {msg_type}")
                        
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON message")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                
    except Exception as e:
        logger.error(f"Connection error: {e}")
        # Try to reconnect after a delay
        await asyncio.sleep(5)
        return await connect_to_ws_server(uri)

async def handle_llm_request(websocket, data):
    """Handle an LLM request by sending a fallback response."""
    try:
        # Extract query from the request
        payload = data.get('payload', {})
        query = payload.get('query', '')
        
        if not query:
            logger.warning("Received LLM request with empty query")
            return
            
        logger.info(f"Processing query: {query}")
        
        # Generate fallback response
        response = generate_fallback_response(query)
        
        # Send response back
        response_message = {
            "type": "query_response",
            "payload": {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "is_fallback": True
            }
        }
        
        logger.info(f"Sending fallback response: {response[:50]}...")
        await websocket.send(json.dumps(response_message))
        logger.info("Fallback response sent successfully")
        
    except Exception as e:
        logger.error(f"Error handling LLM request: {e}")

def generate_fallback_response(query):
    """Generate a fallback response based on the query."""
    # Simple keyword matching
    query_lower = query.lower()
    
    # Check for specific query patterns
    if "example" in query_lower or "show me" in query_lower or "what can you do" in query_lower:
        return random.choice(FALLBACK_RESPONSES)
    elif "help" in query_lower:
        return "I can help you with a variety of tasks including monitoring your screen content, tracking running applications, and providing context-aware assistance. What specific help do you need?"
    elif "how" in query_lower and "work" in query_lower:
        return "This system works by collecting data from various sensors like your screen content and running processes. It then uses this context to provide more relevant assistance. Currently I'm operating in fallback mode due to the LLM service being unavailable."
    else:
        # Generic response
        return f"I've received your query about '{query}'. I'm currently operating in fallback mode as the main LLM service is experiencing delays. Once the service is back up, you'll get more advanced responses. In the meantime, I can still help with basic information and context tracking."

async def main():
    """Main entry point."""
    try:
        # Try both WebSocket servers
        ports = [8765, 8767]
        tasks = []
        
        for port in ports:
            uri = f"ws://localhost:{port}"
            tasks.append(connect_to_ws_server(uri))
            
        # Start all connection tasks
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("Fallback service stopped by user")
    except Exception as e:
        logger.error(f"Unhandled error in main: {e}")
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Fallback service stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")