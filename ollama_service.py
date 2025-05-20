#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
import aiohttp
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/ollama_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ollama_service')

class OllamaLLM:
    def __init__(self, server_uri="ws://localhost:8765", ollama_url="http://localhost:11434"):
        self.server_uri = server_uri
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:latest"  # This should match the model name from API listing
        self.running = True
        self.context_data = {}
        
    async def generate_response(self, query, context=None):
        """Generate a response using Ollama API"""
        try:
            # Build context string from available data
            context_str = ""
            if context:
                if "screen" in context:
                    context_str += f"Active application: {context.get('screen', {}).get('active_app', 'unknown')}\n"
                
                if "processes" in context and context["processes"]:
                    context_str += "Running processes: "
                    proc_names = [p.get("name", "unknown") for p in context["processes"][:5]]
                    context_str += ", ".join(proc_names) + "\n"
            
            # Prepare prompt with context
            if context_str:
                prompt = f"Context information:\n{context_str}\n\nUser query: {query}"
            else:
                prompt = query
            
            # Models to try in order
            models_to_try = [
                self.model_name,  # Try the specified model first
                "llama3.2:latest",  # Then try llama3.2
                "llama3:latest",  # Then try llama3
                "llava:latest"    # Finally try llava
            ]
            
            # Try each model in sequence
            for model in models_to_try:
                try:
                    logger.info(f"Trying model: {model}")
                    
                    # Call Ollama API
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": model,
                            "prompt": prompt,
                            "stream": False
                        }
                        
                        start_time = datetime.now()
                        async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                processing_time = (datetime.now() - start_time).total_seconds()
                                
                                logger.info(f"Generated response with {model} in {processing_time:.2f}s")
                                
                                # Update model name to the one that worked
                                if model != self.model_name:
                                    logger.info(f"Updating default model to {model}")
                                    self.model_name = model
                                
                                return {
                                    "response": result.get("response", "No response generated"),
                                    "model": model,
                                    "context_used": bool(context),
                                    "processing_time": processing_time,
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                error_text = await resp.text()
                                logger.warning(f"Model {model} failed with: {resp.status} - {error_text}")
                except Exception as e:
                    logger.warning(f"Error trying model {model}: {e}")
            
            # If we get here, all models failed
            logger.error("All models failed to generate a response")
            return {
                "response": "I'm sorry, I wasn't able to generate a response at this time. All available language models failed to process your request.",
                "model": "none",
                "error": True,
                "context_used": bool(context),
                "processing_time": 0,
                "timestamp": datetime.now().isoformat()
            }
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(traceback.format_exc())
            return {
                "response": f"Sorry, I encountered an error while generating a response: {str(e)}",
                "model": self.model_name,
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def connect_to_server(self):
        """Connect to the bridge server"""
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "ollama_llm_service",
                            "version": "1.0.0",
                            "model": self.model_name,
                            "capabilities": ["text_generation", "context_aware"]
                        }
                    }))
                    
                    # Main message handling loop
                    while self.running:
                        try:
                            # Receive messages from server
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Process different message types
                            msg_type = data.get('type')
                            
                            if msg_type == 'sensor_data':
                                # Update context data from sensors
                                self.context_data = data.get('payload', {})
                                logger.debug("Context data updated")
                                
                            elif msg_type == 'llm_request':
                                # Process LLM request
                                payload = data.get('payload', {})
                                query = payload.get('query', '')
                                
                                logger.info(f"Processing LLM request: {query[:50]}...")
                                
                                # Generate response
                                llm_response = await self.generate_response(query, self.context_data)
                                
                                # Send response back
                                await websocket.send(json.dumps({
                                    "type": "llm_response",
                                    "payload": llm_response,
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                                logger.info(f"LLM response sent: {llm_response['response'][:50]}...")
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            logger.error(traceback.format_exc())
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def find_available_models(self):
        """Find available Ollama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Available models: {data}")
                        
                        if "models" in data and data["models"]:
                            models = data["models"]
                            available_models = [model["name"] for model in models]
                            logger.info(f"Found {len(available_models)} models: {available_models}")
                            
                            # Try to find the best model in this order of preference
                            preferred_models = ["llama3.2:latest", "llama3:latest", "mistral:latest", "llava:latest"]
                            
                            for preferred in preferred_models:
                                if preferred in available_models:
                                    self.model_name = preferred
                                    logger.info(f"Selected model: {self.model_name}")
                                    return
                            
                            # If none of our preferred models are available, use the first one
                            self.model_name = available_models[0]
                            logger.info(f"Using first available model: {self.model_name}")
                        else:
                            logger.warning("No models found in Ollama")
                    else:
                        logger.error(f"Failed to fetch models: {resp.status}")
        except Exception as e:
            logger.error(f"Error finding available models: {e}")
            logger.error(traceback.format_exc())
    
    async def run(self):
        """Main method to run the LLM service"""
        logger.info(f"Starting Ollama LLM service with initial model {self.model_name}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/ollama_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Find available models
        await self.find_available_models()
        logger.info(f"Using model: {self.model_name}")
        
        # Connect to server
        await self.connect_to_server()

# Function to run the LLM service
async def run_ollama_service():
    llm = OllamaLLM()
    await llm.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_ollama_service())
    except KeyboardInterrupt:
        logger.info("Ollama service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Ollama service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)