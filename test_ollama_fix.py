#!/usr/bin/env python3
"""
Test and fix Ollama JSON parsing issues
"""

import asyncio
import aiohttp
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ollama_api():
    """Test Ollama API with streaming and non-streaming modes"""
    base_url = "http://localhost:11434/api"
    
    # Test 1: Check if service is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    logger.info(f"Ollama service is running. Version: {version_data.get('version')}")
                else:
                    logger.error(f"Ollama service returned status {response.status}")
                    return
    except Exception as e:
        logger.error(f"Failed to connect to Ollama service: {e}")
        return
    
    # Test 2: Test non-streaming mode (should work fine)
    try:
        logger.info("Testing non-streaming mode...")
        request_data = {
            "model": "llama3.2:1b",
            "prompt": "Hello, how are you?",
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/generate", json=request_data) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        logger.info(f"Non-streaming response received: {data['response'][:50]}...")
                    except Exception as e:
                        logger.error(f"Error parsing JSON from non-streaming response: {e}")
                        logger.info(f"Content type: {response.headers.get('Content-Type')}")
                        text = await response.text()
                        logger.info(f"Raw response (first 100 chars): {text[:100]}...")
                else:
                    logger.error(f"Non-streaming request failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error in non-streaming test: {e}")
    
    # Test 3: Test streaming mode (where JSON parsing issues likely occur)
    try:
        logger.info("Testing streaming mode...")
        request_data = {
            "model": "llama3.2:1b",
            "messages": [
                {"role": "user", "content": "Write a short poem about coding"}
            ],
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/chat", json=request_data) as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    logger.info(f"Content type: {content_type}")
                    
                    if 'application/x-ndjson' in content_type:
                        logger.info("Detected NDJSON format - this requires special handling")
                        
                        # Read the stream and handle NDJSON format
                        all_text = ""
                        full_response = ""
                        
                        async for line in response.content:
                            line_text = line.decode('utf-8').strip()
                            all_text += line_text + "\n"
                            
                            if not line_text:
                                continue
                                
                            try:
                                # Parse each line as a separate JSON object
                                data = json.loads(line_text)
                                if 'message' in data and 'content' in data['message']:
                                    content = data['message']['content']
                                    full_response += content
                                    logger.info(f"Got partial response: {content}")
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error on line: {line_text[:50]}... - {e}")
                        
                        logger.info(f"Successfully processed NDJSON stream")
                        logger.info(f"Full response: {full_response}")
                    else:
                        # Try to parse as regular JSON (likely to fail for streaming)
                        try:
                            data = await response.json()
                            logger.info(f"Streaming response received as JSON: {data}")
                        except Exception as e:
                            logger.error(f"Error parsing JSON from streaming response: {e}")
                            text = await response.text()
                            logger.info(f"Raw response (first 100 chars): {text[:100]}...")
                else:
                    logger.error(f"Streaming request failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error in streaming test: {e}")
    
    # Test 4: Implement the fixed streaming parser approach
    try:
        logger.info("Testing fixed streaming approach...")
        request_data = {
            "model": "llama3.2:1b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the capital of France?"}
            ],
            "stream": True
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/chat", json=request_data) as response:
                if response.status == 200:
                    # FIXED APPROACH: Always use text() and parse each line manually
                    content_type = response.headers.get('Content-Type', '')
                    logger.info(f"Fixed approach - Content type: {content_type}")
                    
                    # Read the complete response as text
                    full_text = await response.text()
                    logger.info(f"Got complete response text with length: {len(full_text)}")
                    
                    # Split by lines and parse each line as JSON
                    lines = [line for line in full_text.split('\n') if line.strip()]
                    logger.info(f"Found {len(lines)} JSON objects in the stream")
                    
                    # Process each line
                    full_response = ""
                    for i, line in enumerate(lines):
                        try:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                                full_response += content
                        except json.JSONDecodeError as e:
                            logger.error(f"Line {i}: JSON parse error: {e} - Line: {line[:50]}...")
                    
                    # Extract the main response parts
                    logger.info(f"Fixed approach successfully parsed {len(lines)} JSON objects")
                    logger.info(f"Completed in {time.time() - start_time:.2f}s")
                    logger.info(f"Extracted response: {full_response}")
                else:
                    logger.error(f"Fixed approach request failed with status {response.status}")
    except Exception as e:
        logger.error(f"Error in fixed approach test: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_api())