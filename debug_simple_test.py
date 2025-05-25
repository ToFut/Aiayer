#!/usr/bin/env python3
"""
Debug simple test - minimal working example
"""

import asyncio
import websockets
import json
import aiohttp
from datetime import datetime

async def test_direct_ollama():
    """Test direct Ollama connection with async"""
    print("Testing direct Ollama connection...")
    
    payload = {
        "model": "llama3.2:1b",
        "prompt": "What is 2+2?",
        "stream": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Direct Ollama works: {result.get('response', 'No response')}")
                    return True
                else:
                    print(f"❌ Ollama failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return False

async def test_backend_connection():
    """Test basic backend connection"""
    print("\nTesting backend connection...")
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            connection_data = json.loads(connection_msg)
            print(f"✅ Backend connected: {connection_data.get('message')}")
            
            # Check Ollama availability
            ollama_available = connection_data.get('ai_features', {}).get('ollama_available', False)
            print(f"Ollama available: {ollama_available}")
            
            return True
            
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False

async def test_simple_chat():
    """Test simple chat request"""
    print("\nTesting simple chat request...")
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            print("Connected to backend")
            
            # Send simple request
            request = {
                "type": "chat_request",
                "mode": "ask",
                "message": "What is 2+2?",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(request))
            print("Request sent, waiting for response...")
            
            # Wait for responses
            response_count = 0
            while response_count < 10:  # Limit responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    response_type = response_data.get("type")
                    response_count += 1
                    
                    print(f"Response {response_count}: {response_type}")
                    
                    if response_type == "chat_response_start":
                        print(f"  Start: {response_data.get('message')}")
                    elif response_type == "chat_response_chunk":
                        chunk = response_data.get("chunk", "")
                        print(f"  Chunk: '{chunk}'")
                    elif response_type == "chat_response_complete":
                        full_response = response_data.get("full_response", "")
                        print(f"  ✅ Complete: {full_response}")
                        return True
                    elif response_type == "chat_response_error":
                        error = response_data.get("error", "Unknown error")
                        print(f"  ❌ Error: {error}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("  ⏱️ Response timeout")
                    break
            
            print("❌ No complete response received")
            return False
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False

async def main():
    print("DEBUGGING CHAT SYSTEM")
    print("=" * 40)
    
    # Test 1: Direct Ollama
    ollama_works = await test_direct_ollama()
    
    # Test 2: Backend connection
    backend_works = await test_backend_connection()
    
    # Test 3: Simple chat
    if ollama_works and backend_works:
        chat_works = await test_simple_chat()
        
        if chat_works:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n❌ Chat functionality broken")
    else:
        print("\n❌ Basic components not working")

if __name__ == "__main__":
    asyncio.run(main())