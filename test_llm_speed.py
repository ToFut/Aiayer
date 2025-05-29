#!/usr/bin/env python3
"""
Test LLM Speed - Check ollama3.2:1b response times
"""

import asyncio
import time
import logging
import aiohttp
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ollama_directly():
    """Test Ollama API directly"""
    logger.info("🧪 Testing Ollama API directly...")
    
    # Test 1: Check Ollama is running
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.get("http://localhost:11434/api/version", timeout=5) as response:
                if response.status == 200:
                    version_data = await response.json()
                    elapsed = time.time() - start_time
                    logger.info(f"✅ Ollama is running: {version_data} ({elapsed:.2f}s)")
                else:
                    logger.error(f"❌ Ollama not responding: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    # Test 2: Check available models
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=5) as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [model['name'] for model in models_data.get('models', [])]
                    logger.info(f"📋 Available models: {models}")
                    
                    # Check for fast models
                    if "llama3.2:1b" in models:
                        logger.info("✅ llama3.2:1b is available")
                        target_model = "llama3.2:1b"
                    elif "llama3.2:latest" in models:
                        logger.info("⚠️ Using llama3.2:latest instead of 1b")
                        target_model = "llama3.2:latest"
                    else:
                        logger.error("❌ No suitable model found")
                        return False
                else:
                    logger.error(f"❌ Cannot get models: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Error getting models: {e}")
        return False
    
    # Test 3: Test response speed with simple query
    test_queries = [
        "Hello",
        "What is 2+2?",
        "Briefly explain what AI is in one sentence."
    ]
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n🧪 Test {i}: '{query}'")
        
        request_data = {
            "model": target_model,
            "messages": [
                {"role": "user", "content": query}
            ],
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.post(
                    "http://localhost:11434/api/chat",
                    json=request_data,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        elapsed = time.time() - start_time
                        
                        if 'message' in data and 'content' in data['message']:
                            response_text = data['message']['content']
                            logger.info(f"✅ Response in {elapsed:.2f}s: {response_text[:100]}...")
                            
                            # Check if response time is acceptable
                            if elapsed <= 10:
                                logger.info(f"✅ GOOD: Response within 10s")
                            elif elapsed <= 25:
                                logger.info(f"⚠️ SLOW: Response within 25s but slower than expected")
                            else:
                                logger.error(f"❌ TOO SLOW: Response took {elapsed:.2f}s")
                        else:
                            logger.error(f"❌ Invalid response format: {data}")
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
                        
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"❌ TIMEOUT: Request took more than 30s ({elapsed:.2f}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ ERROR after {elapsed:.2f}s: {e}")
    
    return True

async def test_ollama_streaming():
    """Test Ollama streaming response"""
    logger.info("\n🧪 Testing Ollama streaming...")
    
    request_data = {
        "model": "llama3.2:1b",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5 with explanations"}
        ],
        "stream": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            first_chunk_time = None
            chunks_received = 0
            
            async with session.post(
                "http://localhost:11434/api/chat",
                json=request_data,
                timeout=30
            ) as response:
                
                if response.status == 200:
                    logger.info("📡 Streaming response started...")
                    
                    async for line in response.content:
                        if line:
                            chunks_received += 1
                            if first_chunk_time is None:
                                first_chunk_time = time.time() - start_time
                                logger.info(f"⚡ First chunk received in {first_chunk_time:.2f}s")
                            
                            try:
                                data = json.loads(line)
                                if 'message' in data and 'content' in data['message']:
                                    content = data['message']['content']
                                    if content.strip():
                                        print(content, end='', flush=True)
                                
                                if data.get('done'):
                                    total_time = time.time() - start_time
                                    print(f"\n✅ Streaming complete in {total_time:.2f}s ({chunks_received} chunks)")
                                    
                                    if first_chunk_time <= 10:
                                        logger.info("✅ GOOD: First chunk within 10s")
                                    else:
                                        logger.error(f"❌ SLOW: First chunk took {first_chunk_time:.2f}s")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                else:
                    logger.error(f"❌ Streaming failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 LLM Speed Test Starting...")
    logger.info("Expected: ollama3.2:1b should stream within 10s, complete within 25s")
    
    # Test direct API
    if await test_ollama_directly():
        # Test streaming
        await test_ollama_streaming()
    
    logger.info("\n🏁 LLM Speed Test Complete")

if __name__ == "__main__":
    asyncio.run(main())