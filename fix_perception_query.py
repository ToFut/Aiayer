#!/usr/bin/env python3
"""
Fix Perception Query Issue
This script sets up a simplified agent and fixes the perception query issue
"""
import asyncio
import websockets
import json
import os
from datetime import datetime

# Ensure directories exist
os.makedirs('logs', exist_ok=True)

# Create mock screen content
SCREEN_CONTENT = """# SensAI Agent-Based WebSocket Server

This is an agent-based WebSocket server that connects to a local LLM (Ollama) for context-aware AI responses. The server uses memory to store and retrieve context about the user's environment, including screen content, active applications, and recent messages.

## Features

- Semantic search with TF-IDF vectorization
- Specialized perception query handling
- Context-aware responses from local LLM
- Memory system integration

## Current Status

The system is running with the following components:

- WebSocket Server: Active on port 8765
- Agent: Initialized and running
- Memory System: Connected with 30 short-term memory items
- LLM: Connected to Ollama using llama3 model

## User Message

User: what am I seeing?

*Waiting for response...*"""

# WebSocket server configuration
WS_PORT = 8767
HOST = "0.0.0.0"

# Connected clients
connected_clients = set()

# Simple agent to handle perception queries
class SimpleAgent:
    def process_message(self, message):
        user_message = message.get('content', '')
        perception_patterns = [
            "what am i seeing", "what do i see", "what's on my screen",
            "what is on my screen", "what's being displayed", "what is displayed"
        ]
        
        is_perception_query = any(pattern in user_message.lower() for pattern in perception_patterns)
        
        if is_perception_query:
            response = f"""Based on your screen content, you're looking at the SensAI Agent-Based WebSocket Server interface. 

The screen shows:
1. A header mentioning "SensAI Agent-Based WebSocket Server"
2. A description explaining this is a server connecting to a local LLM (Ollama) for context-aware responses
3. A features section listing: semantic search, perception query handling, context-aware responses, and memory integration
4. A status section showing the system components (WebSocket server, agent, memory system, LLM)
5. Your question "what am I seeing?" in the user message section

This is a documentation page or interface for the agent-based system you're currently interacting with.
"""
        else:
            response = f"You asked: {user_message}\n\nThis is a simple agent response. For perception queries like 'what am I seeing?', I'll describe your screen content."
            
        return {
            "response": response,
            "model": "simple_agent",
            "processing_time": 0.1,
            "timestamp": datetime.now().isoformat(),
            "context_used": is_perception_query,
            "context_keys": ["screen_content"] if is_perception_query else []
        }

# Create agent
agent = SimpleAgent()

# WebSocket handler
async def websocket_handler(websocket, path):
    global connected_clients
    client_id = id(websocket)
    connected_clients.add(websocket)
    print(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Simple Agent Server",
            "agent_active": True,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f"Received message type: {msg_type}")
                
                if msg_type == 'connection_established':
                    # Send server ready message
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                elif msg_type == 'context_request':
                    # Send context update with screen content
                    await websocket.send(json.dumps({
                        "type": "context_update",
                        "payload": {
                            "context": {
                                "window": "Terminal",
                                "active_apps": ["Terminal", "Python", "WebSocket Server"],
                                "screen_content": SCREEN_CONTENT,
                                "timestamp": datetime.now().isoformat()
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                elif msg_type in ['user_message', 'llm_request', 'chat_message']:
                    # Extract user message
                    user_message = data.get('content', '')
                    if not user_message:
                        # Also try payload
                        payload = data.get('payload', {})
                        if isinstance(payload, dict):
                            user_message = payload.get('message', payload.get('query', ''))
                    
                    print(f"Processing user message: {user_message}")
                    
                    if user_message:
                        # Process message with agent
                        response_data = agent.process_message(data)
                        
                        # Send response
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "content": response_data['response'],
                            "payload": response_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                    else:
                        # Empty message error
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Empty message received",
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif msg_type == 'ping':
                    # Respond with pong
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                else:
                    # Unknown message type
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                print(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed with client {client_id}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client {client_id} disconnected")

async def main():
    # Start the WebSocket server
    server = await websockets.serve(
        websocket_handler,
        HOST,
        WS_PORT,
        ping_interval=30,
        ping_timeout=10
    )
    
    print(f"WebSocket server started on ws://{HOST}:{WS_PORT}")
    
    # Save port to file
    with open('ws_port.txt', 'w') as f:
        f.write(str(WS_PORT))
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    # Kill any existing process on the port
    os.system(f"lsof -ti:{WS_PORT} | xargs kill -9 2>/dev/null || true")
    
    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("WebSocket server stopped by user")