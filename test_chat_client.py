#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_chat():
    try:
        print("Connecting to WebSocket server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("Connection established!")
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "version": "1.0.0",
                    "capabilities": ["test"],
                    "timestamp": time.time()
                }
            }))
            
            # Wait for welcome response
            response = await websocket.recv()
            print(f"Received initial response: {response}")
            
            # Send a chat message
            message = json.dumps({
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "Hello, are you working properly? I'm trying to use the chat."
                }
            })
            
            print(f"Sending message: {message}")
            await websocket.send(message)
            
            # Wait for response
            print("Waiting for response...")
            chat_response = await websocket.recv()
            print(f"Received chat response: {chat_response}")
            
            # Test ping/pong
            await websocket.send(json.dumps({
                "type": "ping",
                "payload": {
                    "timestamp": time.time()
                }
            }))
            
            # Wait for pong
            pong_response = await websocket.recv()
            print(f"Received pong: {pong_response}")
            
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_chat())