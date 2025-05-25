#!/usr/bin/env python3
"""
Test Ollama streaming directly to understand the format
"""

import asyncio
import aiohttp
import json

async def test_ollama_streaming():
    """Test Ollama streaming response format"""
    
    payload = {
        "model": "llama3.2:1b",
        "prompt": "What is 2+2?",
        "stream": True
    }
    
    print("Testing Ollama streaming format...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    full_response = ""
                    chunk_count = 0
                    
                    async for line in response.content:
                        if line:
                            try:
                                line_text = line.decode('utf-8').strip()
                                if line_text:
                                    chunk_data = json.loads(line_text)
                                    chunk_count += 1
                                    
                                    print(f"Chunk {chunk_count}:")
                                    print(f"  Response: '{chunk_data.get('response', '')}'")
                                    print(f"  Done: {chunk_data.get('done', False)}")
                                    
                                    if chunk_data.get("response"):
                                        full_response += chunk_data.get("response", "")
                                    
                                    # Check if done
                                    if chunk_data.get("done", False):
                                        print(f"\n✅ Complete response: '{full_response}'")
                                        return True
                                        
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")
                                continue
                    
                    print(f"\n⚠️ Stream ended without done flag. Response: '{full_response}'")
                    return False
                else:
                    print(f"❌ HTTP error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ollama_streaming())