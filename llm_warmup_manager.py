#!/usr/bin/env python3
"""
LLM Warmup Manager
Keeps ollama3.2:1b model loaded and warm for fast responses
"""

import asyncio
import time
import logging
import aiohttp
import json
import signal
import atexit
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWarmupManager:
    """Singleton manager to keep LLM models warm and ready"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMWarmupManager, cls).__new__(cls)
        return cls._instance
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.warmup_running:
            await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    def __init__(self):
        if self._initialized:
            return
            
        self.base_url = "http://localhost:11434"
        self.preferred_model = "llama3.2:1b"
        self.fallback_model = "llama3.2:latest"
        self.current_model = None
        self.model_warm = False
        self.warmup_running = False
        self.last_request_time = 0
        self.warmup_interval = 300  # Keep warm every 5 minutes
        
        # Shared session for all requests
        self.session = None
        
        self._initialized = True
        
        # Register cleanup handlers
        atexit.register(self._cleanup_sync)
        
        logger.info("🔥 LLM Warmup Manager initialized")
    
    async def start(self):
        """Start the warmup manager"""
        if self.warmup_running:
            return True
            
        try:
            # Create persistent session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Initial warmup
            success = await self.warmup_model()
            if success:
                self.warmup_running = True
                
                # Start background warmup task
                asyncio.create_task(self._background_warmup())
                logger.info("🔥 LLM Warmup Manager started successfully")
                return True
            else:
                logger.error("❌ Failed to start LLM Warmup Manager")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting warmup manager: {e}")
            return False
    
    async def stop(self):
        """Stop the warmup manager"""
        self.warmup_running = False
        if self.session:
            try:
                await self.session.close()
                # Wait a bit for the session to properly close
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self.session = None
        logger.info("🛑 LLM Warmup Manager stopped")
    
    def _cleanup_sync(self):
        """Synchronous cleanup for atexit"""
        if self.session and not self.session.closed:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.session.close())
                loop.close()
            except Exception:
                pass  # Ignore cleanup errors during shutdown
    
    async def warmup_model(self):
        """Warm up the model with a quick request"""
        try:
            logger.info("🔥 Warming up model...")
            
            # Check available models
            model_to_use = await self._get_best_model()
            if not model_to_use:
                logger.error("❌ No suitable model available")
                return False
            
            self.current_model = model_to_use
            
            # Forceful warmup request - send multiple messages to ensure model is loaded
            for i in range(2):  # Try warming up twice to ensure it's ready
                warmup_request = {
                    "model": model_to_use,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": f"Respond with 'LLM is warm and ready (test {i+1})' to confirm you're working."}
                    ],
                    "stream": False
                }
                
                start_time = time.time()
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/chat",
                        json=warmup_request,
                        timeout=aiohttp.ClientTimeout(total=15)  # Increased timeout for first warmup
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            elapsed = time.time() - start_time
                            
                            if 'message' in data and 'content' in data['message']:
                                response_text = data['message']['content']
                                
                                # Verify it's not a mock response
                                if "LLM is warm" in response_text or "ready" in response_text.lower():
                                    self.model_warm = True
                                    self.last_request_time = time.time()
                                    logger.info(f"✅ Model {model_to_use} successfully warmed up in {elapsed:.2f}s")
                                    logger.info(f"✅ Response: {response_text[:50]}")
                                    return True
                                else:
                                    logger.warning(f"⚠️ Model responded but may not be fully warmed up: {response_text[:50]}...")
                                    # Continue to next attempt
                            else:
                                logger.warning("⚠️ Warmup response doesn't contain message content")
                                # Continue to next attempt
                        else:
                            logger.warning(f"⚠️ Warmup attempt {i+1} failed: HTTP {response.status}")
                            # Continue to next attempt
                except Exception as req_err:
                    logger.warning(f"⚠️ Warmup request {i+1} failed: {req_err}")
                    # Continue to next attempt
                
                # Short wait between attempts
                await asyncio.sleep(1)
            
            # If we get here, both attempts failed
            logger.error("❌ Failed to properly warm up the model after multiple attempts")
            return False
                    
        except Exception as e:
            logger.error(f"❌ Warmup error: {e}")
            return False
    
    async def _get_best_model(self):
        """Get the best available model"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [model['name'] for model in models_data.get('models', [])]
                    
                    # Prefer 1b model for speed
                    if self.preferred_model in models:
                        logger.info(f"✅ Using fast model: {self.preferred_model}")
                        return self.preferred_model
                    elif self.fallback_model in models:
                        logger.info(f"⚠️ Using fallback model: {self.fallback_model}")
                        return self.fallback_model
                    else:
                        logger.error("❌ No suitable model found")
                        return None
                else:
                    logger.error("❌ Cannot get models list")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting models: {e}")
            return None
    
    async def _background_warmup(self):
        """Background task to keep model warm"""
        while self.warmup_running:
            try:
                await asyncio.sleep(self.warmup_interval)
                
                if self.warmup_running:
                    # Check if model needs warming
                    time_since_last = time.time() - self.last_request_time
                    if time_since_last > self.warmup_interval:
                        logger.info("🔥 Refreshing model warmup...")
                        await self.warmup_model()
                        
            except Exception as e:
                logger.error(f"❌ Background warmup error: {e}")
    
    async def fast_generate_response(self, messages: list, max_tokens: int = 2048, temperature: float = 0.8):
        """Generate response using warmed model"""
        if not self.model_warm or not self.current_model:
            logger.warning("⚠️ Model not warm, warming up...")
            success = await self.warmup_model()
            if not success:
                return "Error: Model not available"
        
        try:
            request_data = {
                "model": self.current_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Create a new session for each request to avoid connection issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as request_session:
                start_time = time.time()
                async with request_session.post(
                    f"{self.base_url}/api/chat",
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        elapsed = time.time() - start_time
                        self.last_request_time = time.time()
                        
                        if 'message' in data and 'content' in data['message']:
                            response_text = data['message']['content']
                            logger.info(f"⚡ Fast response in {elapsed:.2f}s")
                            return response_text
                        else:
                            logger.error("❌ Invalid response format")
                            return "Error: Invalid response format"
                    else:
                        logger.error(f"❌ Request failed: HTTP {response.status}")
                        return f"Error: HTTP {response.status}"
                    
        except Exception as e:
            logger.error(f"❌ Fast generate error: {e}")
            return f"Error: {str(e)}"
    
    def is_model_warm(self):
        """Check if model is warm and ready"""
        return self.model_warm and self.current_model
    
    def get_current_model(self):
        """Get currently loaded model"""
        return self.current_model
    
    async def generate_fast_automation_plan(self, instruction: str):
        """Generate automation plan using fast LLM with minimal overhead"""
        try:
            # Simple automation plan prompt optimized for speed
            messages = [
                {
                    "role": "system", 
                    "content": "Create a concise automation plan. Response format: {\"title\": \"Task\", \"steps\": [{\"id\": \"1\", \"description\": \"Step\", \"action_type\": \"click|type|scroll\", \"target\": \"element\", \"value\": \"\"}]}"
                },
                {
                    "role": "user",
                    "content": f"Create automation plan for: {instruction}"
                }
            ]
            
            # Use fast generation with minimal tokens for speed
            response = await self.fast_generate_response(messages, max_tokens=500, temperature=0.3)
            
            if response and not response.startswith("Error:"):
                try:
                    # Try to extract JSON from response
                    import json
                    import re
                    
                    # Extract JSON from response (handle potential markdown)
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        plan_data = json.loads(json_match.group())
                        
                        # Create simplified plan object
                        class SimplePlan:
                            def __init__(self, data):
                                self.title = data.get("title", instruction)
                                self.steps = []
                                for i, step in enumerate(data.get("steps", [])):
                                    step_obj = type('Step', (), {
                                        'id': step.get("id", f"step_{i}"),
                                        'description': step.get("description", "Execute action"),
                                        'action_type': step.get("action_type", "click"),
                                        'target': step.get("target", "element"),
                                        'value': step.get("value", ""),
                                        'estimated_duration': 2
                                    })()
                                    self.steps.append(step_obj)
                                self.complexity_score = 0.8
                        
                        logger.info(f"⚡ Fast automation plan created: {plan_data.get('title', instruction)}")
                        return SimplePlan(plan_data)
                    
                except Exception as parse_error:
                    logger.warning(f"Failed to parse fast plan, creating fallback: {parse_error}")
                
                # Fallback: create simple plan from instruction
                class SimplePlan:
                    def __init__(self, instruction):
                        self.title = instruction
                        self.steps = [
                            type('Step', (), {
                                'id': 'step_1',
                                'description': f"Analyze screen for: {instruction}",
                                'action_type': 'analyze',
                                'target': 'screen',
                                'value': '',
                                'estimated_duration': 1
                            })(),
                            type('Step', (), {
                                'id': 'step_2', 
                                'description': f"Execute: {instruction}",
                                'action_type': 'click',
                                'target': 'detected_element',
                                'value': '',
                                'estimated_duration': 2
                            })()
                        ]
                        self.complexity_score = 0.7
                
                return SimplePlan(instruction)
            
            return None
            
        except Exception as e:
            logger.error(f"Fast automation plan generation failed: {e}")
            return None

# Global singleton instance
_warmup_manager = None

async def get_warmup_manager():
    """Get or create the global warmup manager"""
    global _warmup_manager
    if _warmup_manager is None:
        _warmup_manager = LLMWarmupManager()
        await _warmup_manager.start()
    return _warmup_manager

async def test_warmup_manager():
    """Test the warmup manager"""
    logger.info("🧪 Testing LLM Warmup Manager...")
    
    manager = await get_warmup_manager()
    
    if manager.is_model_warm():
        logger.info(f"✅ Model {manager.get_current_model()} is warm and ready")
        
        # Test fast response
        test_messages = [
            {"role": "user", "content": "What is 5+3?"}
        ]
        
        response = await manager.fast_generate_response(test_messages)
        logger.info(f"📝 Test response: {response}")
    else:
        logger.error("❌ Model is not warm")
    
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(test_warmup_manager())