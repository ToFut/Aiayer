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
        self.model_name = "ollama:latest3.2"  # Use the specified model
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
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                start_time = datetime.now()
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return {
                            "response": f"Error generating response: {resp.status}",
                            "model": self.model_name,
                            "context_used": bool(context),
                            "processing_time": 0,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    result = await resp.json()
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Generated response in {processing_time:.2f}s")
                    
                    return {
                        "response": result.get("response", "No response generated"),
                        "model": self.model_name,
                        "context_used": bool(context),
                        "processing_time": processing_time,
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
    
    async def run(self):
        """Main method to run the LLM service"""
        logger.info(f"Starting Ollama LLM service with model {self.model_name}")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/ollama_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
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