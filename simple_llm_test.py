#!/usr/bin/env python3
"""
Simple LLM Response Time Test
Tests the basic LLM response time using direct Ollama API calls
"""

import asyncio
import aiohttp
import time
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_direct_ollama():
    """Test direct Ollama API response time"""
    logger.info("🔍 Testing direct Ollama API response time...")
    
    base_url = "http://localhost:11434/api"
    results = []
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check available models
            logger.info("Checking available models...")
            async with session.get(f"{base_url}/tags") as response:
                models_data = await response.json()
                models = models_data.get('models', [])
                
                if not models:
                    logger.error("No models found!")
                    return []
                
                logger.info(f"Found {len(models)} models:")
                for model in models:
                    size_gb = model.get('size', 0) / (1024**3)  # Convert to GB
                    logger.info(f"- {model.get('name')}: {size_gb:.1f}GB")
            
            # Test prompts
            test_prompts = [
                {"prompt": "Hello, how are you?", "name": "Simple Greeting"},
                {"prompt": "Create a step-by-step plan to search for Python tutorials online", 
                 "name": "Simple Plan"},
                {"prompt": "What is the capital of France?", "name": "Simple Question"}
            ]
            
            # Test with default model
            default_model = models[0]['name'] if models else "llama3.2:1b"
            logger.info(f"Using model: {default_model}")
            
            for test in test_prompts:
                logger.info(f"Testing: {test['name']} - \"{test['prompt']}\"")
                
                # Test chat endpoint
                start_time = time.time()
                payload = {
                    "model": default_model,
                    "messages": [
                        {"role": "user", "content": test['prompt']}
                    ],
                    "stream": False
                }
                
                try:
                    async with session.post(
                        f"{base_url}/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        response_data = await response.json()
                        response_time = time.time() - start_time
                        
                        success = "message" in response_data
                        content = response_data.get("message", {}).get("content", "")
                        
                        logger.info(f"Response time: {response_time:.2f}s")
                        logger.info(f"Success: {success}")
                        logger.info(f"Response preview: {content[:100]}...")
                        
                        results.append({
                            "test_name": test['name'],
                            "prompt": test['prompt'],
                            "model": default_model,
                            "response_time": response_time,
                            "success": success,
                            "response_length": len(content) if success else 0
                        })
                        
                except asyncio.TimeoutError:
                    logger.error(f"Request timed out after 60s!")
                    results.append({
                        "test_name": test['name'],
                        "prompt": test['prompt'],
                        "model": default_model,
                        "response_time": 60.0,
                        "success": False,
                        "error": "timeout"
                    })
                
                except Exception as e:
                    logger.error(f"Error: {e}")
                    results.append({
                        "test_name": test['name'],
                        "prompt": test['prompt'],
                        "model": default_model,
                        "response_time": time.time() - start_time,
                        "success": False,
                        "error": str(e)
                    })
                
                # Wait between requests
                await asyncio.sleep(1)
            
            return results
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return []

async def test_fast_model():
    """Test with fastest model (llama3.2:1b)"""
    logger.info("🔍 Testing with fastest model (llama3.2:1b)...")
    
    base_url = "http://localhost:11434/api"
    results = []
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try to use fast model
            fast_model = "llama3.2:1b"
            
            # Test generation endpoint (simpler than chat)
            start_time = time.time()
            payload = {
                "model": fast_model,
                "prompt": "Create a step by step plan to search for Python tutorials online",
                "stream": False
            }
            
            try:
                async with session.post(
                    f"{base_url}/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_data = await response.json()
                    response_time = time.time() - start_time
                    
                    success = "response" in response_data
                    content = response_data.get("response", "")
                    
                    logger.info(f"Response time: {response_time:.2f}s")
                    logger.info(f"Success: {success}")
                    logger.info(f"Response preview: {content[:100]}...")
                    
                    results.append({
                        "test_name": "Fast Model Generate",
                        "model": fast_model,
                        "response_time": response_time,
                        "success": success,
                        "response_length": len(content) if success else 0
                    })
                    
            except asyncio.TimeoutError:
                logger.error(f"Request timed out after 60s!")
                results.append({
                    "test_name": "Fast Model Generate",
                    "model": fast_model,
                    "response_time": 60.0,
                    "success": False,
                    "error": "timeout"
                })
            
            except Exception as e:
                logger.error(f"Error: {e}")
                results.append({
                    "test_name": "Fast Model Generate",
                    "model": fast_model,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return []

async def run_all_tests():
    """Run all timing tests"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Simple LLM Response Time Tests")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: Direct Ollama API
    logger.info("\n📊 TEST 1: Direct Ollama API")
    logger.info("-" * 50)
    ollama_results = await test_direct_ollama()
    results["ollama_direct"] = ollama_results
    logger.info("")
    
    # Test 2: Fast Model Test
    logger.info("\n📊 TEST 2: Fast Model Test")
    logger.info("-" * 50)
    fast_results = await test_fast_model()
    results["fast_model"] = fast_results
    logger.info("")
    
    # Save results
    with open('llm_response_time_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Show summary
    logger.info("=" * 60)
    logger.info("📝 SUMMARY")
    logger.info("=" * 60)
    
    # Ollama API times
    if ollama_results:
        avg_ollama = sum(r["response_time"] for r in ollama_results) / len(ollama_results)
        logger.info(f"Ollama API Avg: {avg_ollama:.2f}s")
        for r in ollama_results:
            logger.info(f"  - {r['test_name']}: {r['response_time']:.2f}s")
    
    # Fast model times
    if fast_results:
        avg_fast = sum(r["response_time"] for r in fast_results) / len(fast_results)
        logger.info(f"Fast Model Avg: {avg_fast:.2f}s")
        for r in fast_results:
            logger.info(f"  - {r['test_name']}: {r['response_time']:.2f}s")
    
    logger.info("=" * 60)
    logger.info("Results saved to llm_response_time_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())