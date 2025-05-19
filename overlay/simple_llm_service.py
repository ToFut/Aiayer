#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/llm_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('llm_service')

class SimpleLLM:
    def __init__(self, server_uri="ws://localhost:8765"):
        self.server_uri = server_uri
        self.running = True
        self.context_data = {}
        
    async def generate_response(self, query, context=None):
        """Generate a simulated LLM response"""
        # In a real implementation, this would call a real LLM
        response_templates = [
            "Based on your current context, I can see you're working with {app}. {query_response}",
            "I notice you have {process} running. {query_response}",
            "While analyzing your environment, I see {query_response}",
            "Taking into account your current tasks, {query_response}"
        ]
        
        generic_responses = [
            "This is a simulated response to your query about '{query}'.",
            "I would analyze this further if I were connected to a real LLM.",
            "Your question about '{query}' would normally be processed by a language model.",
            "In a full implementation, I would provide detailed information about '{query}'."
        ]
        
        # Get active app from context if available
        active_app = "unknown apps"
        top_process = "various processes"
        
        if context and "screen" in context:
            active_app = context.get("screen", {}).get("active_app", "unknown apps")
            
        if context and "processes" in context and context["processes"]:
            top_process = context["processes"][0]["name"] if context["processes"] else "various processes"
        
        # Select template and response
        import random
        template = random.choice(response_templates)
        query_response = random.choice(generic_responses).format(query=query)
        
        # Format final response
        response = template.format(
            app=active_app,
            process=top_process,
            query_response=query_response
        )
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        return {
            "response": response,
            "model": "simulator-1.0",
            "context_used": bool(context),
            "processing_time": 1.0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def connect_to_server(self):
        """Connect to the bridge server"""
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Process initial welcome message
                    response = await websocket.recv()
                    data = json.loads(response)
                    logger.info(f"Received from server: {data.get('type')}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "llm_service",
                            "version": "1.0.0",
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
        logger.info("Starting LLM service")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/llm_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to server
        await self.connect_to_server()

# Function to run the LLM service
async def run_llm_service():
    llm = SimpleLLM()
    await llm.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_llm_service())
    except KeyboardInterrupt:
        logger.info("LLM service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running LLM service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
