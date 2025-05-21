#!/usr/bin/env python3
"""
Enhanced Ollama LLM Service
Integrates with enhanced context memory system to provide rich context-aware responses.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
import aiohttp
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/enhanced_ollama_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_ollama_service')

class EnhancedOllamaLLM:
    def __init__(self, server_uri="ws://localhost:8767", context_uri="ws://localhost:8769", 
                 ollama_url="http://localhost:11434"):
        self.server_uri = server_uri
        self.context_uri = context_uri  # WebSocket connection to enhanced context service
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:latest"
        self.running = True
        self.raw_context_data = {}
        self.enhanced_context_data = {}
        self.context_websocket = None
        self.last_context_update = 0
        self.context_update_interval = 5  # Seconds between context updates
        self.timeout = 20  # Seconds to wait for LLM response

    async def initialize_context_connection(self):
        """Initialize connection to the enhanced context memory system"""
        try:
            logger.info(f"Connecting to enhanced context system at {self.context_uri}")
            self.context_websocket = await websockets.connect(self.context_uri)
            
            # Send identification
            await self.context_websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "enhanced_ollama_llm_service",
                    "version": "1.0.0",
                    "capabilities": ["context_aware", "llm"]
                }
            }))
            
            # Request initial context
            await self._update_enhanced_context()
            
            logger.info("Connected to enhanced context system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to enhanced context system: {e}")
            logger.error(traceback.format_exc())
            self.context_websocket = None
            return False

    async def _update_enhanced_context(self):
        """Request updated context from the enhanced context memory system"""
        if not self.context_websocket:
            return
            
        current_time = time.time()
        if current_time - self.last_context_update < self.context_update_interval:
            return
            
        try:
            # Request enhanced context
            await self.context_websocket.send(json.dumps({
                "type": "get_enhanced_context",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for response
            response = await asyncio.wait_for(self.context_websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'enhanced_context':
                self.enhanced_context_data = data.get('payload', {})
                self.last_context_update = current_time
                logger.info(f"Enhanced context updated: {len(json.dumps(self.enhanced_context_data))} bytes")
                
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for enhanced context")
        except Exception as e:
            logger.error(f"Error updating enhanced context: {e}")
            logger.error(traceback.format_exc())

    def _build_context_prompt(self, query):
        """
        Build a rich context prompt that includes visual understanding,
        application context, user activities, and relevant background info.
        """
        context_parts = []
        
        # Add standard header
        context_parts.append("# Current Context Information")
        
        # Add enhanced context if available
        if self.enhanced_context_data:
            # Current application
            if "current_application" in self.enhanced_context_data and self.enhanced_context_data["current_application"]:
                app_context = self.enhanced_context_data["current_application"]
                app_section = ["## Current Application"]
                
                if app_context.get("name"):
                    app_section.append(f"Application: {app_context['name']}")
                if app_context.get("window"):
                    app_section.append(f"Window: {app_context['window']}")
                if app_context.get("view"):
                    app_section.append(f"View: {app_context['view']}")
                if app_context.get("workflow"):
                    app_section.append(f"User Task: {app_context['workflow']}")
                
                context_parts.append("\n".join(app_section))
            
            # Screen context (what the user sees)
            if "screen_context" in self.enhanced_context_data and self.enhanced_context_data["screen_context"]:
                screen_context = self.enhanced_context_data["screen_context"]
                screen_section = ["## Visual Information"]
                
                if screen_context.get("visual_description"):
                    # Truncate very long descriptions
                    description = screen_context["visual_description"]
                    if len(description) > 500:
                        description = description[:500] + "..."
                    screen_section.append(description)
                
                # Add UI elements
                if screen_context.get("ui_elements") and isinstance(screen_context["ui_elements"], list):
                    elements = screen_context["ui_elements"]
                    if elements:
                        screen_section.append("Visible UI elements:")
                        for i, element in enumerate(elements[:5]):
                            if isinstance(element, dict):
                                element_type = element.get("type", "element")
                                element_name = element.get("name", "")
                                screen_section.append(f"- {element_name} ({element_type})")
                
                context_parts.append("\n".join(screen_section))
            
            # Email context
            if "email_context" in self.enhanced_context_data and self.enhanced_context_data["email_context"]:
                email_data = self.enhanced_context_data["email_context"]
                email_section = ["## Email Information"]
                
                if email_data.get("from"):
                    email_section.append(f"From: {email_data['from']}")
                if email_data.get("to"):
                    email_section.append(f"To: {email_data['to']}")
                if email_data.get("subject"):
                    email_section.append(f"Subject: {email_data['subject']}")
                
                context_parts.append("\n".join(email_section))
            
            # Form context
            if "form_context" in self.enhanced_context_data and self.enhanced_context_data["form_context"]:
                form_data = self.enhanced_context_data["form_context"]
                if "form_fields" in form_data and form_data["form_fields"]:
                    form_section = ["## Form Information"]
                    form_section.append(f"Form fields: {', '.join(form_data['form_fields'][:5])}")
                    context_parts.append("\n".join(form_section))
            
            # Recent activities
            if "recent_activities" in self.enhanced_context_data and self.enhanced_context_data["recent_activities"]:
                activities = self.enhanced_context_data["recent_activities"]
                if activities:
                    activity_section = ["## Recent User Activities"]
                    
                    for activity in activities[:3]:
                        if isinstance(activity, dict):
                            app = activity.get("application", "")
                            action = activity.get("action", "")
                            summary = activity.get("content_summary", "")
                            
                            if action and app:
                                activity_str = f"- {action} in {app}"
                                if summary:
                                    # Keep summaries short
                                    if len(summary) > 100:
                                        summary = summary[:100] + "..."
                                    activity_str += f": {summary}"
                                activity_section.append(activity_str)
                    
                    context_parts.append("\n".join(activity_section))
        
        # Fall back to raw context if enhanced context is unavailable
        elif self.raw_context_data:
            fallback_sections = ["## System Context (Basic)"]
            
            if "screen" in self.raw_context_data and isinstance(self.raw_context_data["screen"], dict):
                screen_data = self.raw_context_data["screen"]
                if "active_window" in screen_data:
                    fallback_sections.append(f"Active window: {screen_data['active_window']}")
                if "active_app" in screen_data:
                    fallback_sections.append(f"Active application: {screen_data['active_app']}")
            
            if "processes" in self.raw_context_data and self.raw_context_data["processes"]:
                proc_names = [p.get("name", "unknown") for p in self.raw_context_data["processes"][:5]]
                if proc_names:
                    fallback_sections.append(f"Running applications: {', '.join(proc_names)}")
            
            context_parts.append("\n".join(fallback_sections))
        
        # Combine all context parts
        context = "\n\n".join(context_parts)
        
        # Create the final prompt
        final_prompt = f"{context}\n\n# User Query\n{query}"
        return final_prompt

    async def generate_response(self, query, raw_context=None):
        """Generate a response using Ollama API with enhanced context"""
        try:
            # Update raw context if provided
            if raw_context:
                self.raw_context_data = raw_context
            
            # Update enhanced context if needed
            await self._update_enhanced_context()
            
            # Build rich context prompt
            prompt = self._build_context_prompt(query)
            
            # Log prompt details (truncated for brevity)
            logger.info(f"Generated context prompt with {len(prompt)} chars")
            logger.debug(f"Prompt excerpt: {prompt[:500]}...")
            
            # Models to try in order
            models_to_try = [
                self.model_name,      # Try the specified model first
                "llama3.2:latest",    # Then try llama3.2
                "llama3:latest",      # Then try llama3
                "mistral:latest",     # Then try mistral
                "llava:latest"        # Finally try llava
            ]
            
            # Ensure we have a unique list
            models_to_try = list(dict.fromkeys(models_to_try))
            
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
                        try:
                            async with session.post(
                                f"{self.ollama_url}/api/generate", 
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=self.timeout)
                            ) as resp:
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
                                        "context_used": True,
                                        "enhanced_context_used": bool(self.enhanced_context_data),
                                        "processing_time": processing_time,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                else:
                                    error_text = await resp.text()
                                    logger.warning(f"Model {model} failed with: {resp.status} - {error_text}")
                        except asyncio.TimeoutError:
                            logger.warning(f"Request timeout with model {model}")
                except Exception as e:
                    logger.warning(f"Error trying model {model}: {e}")
            
            # If we get here, all models failed
            logger.error("All models failed to generate a response")
            return {
                "response": "I'm sorry, I wasn't able to generate a response at this time. All available language models failed to process your request.",
                "model": "none",
                "error": True,
                "context_used": bool(raw_context or self.raw_context_data),
                "enhanced_context_used": bool(self.enhanced_context_data),
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
                "context_used": False,
                "enhanced_context_used": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def connect_to_bridge_server(self):
        """Connect to the bridge server"""
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "enhanced_ollama_llm_service",
                            "version": "1.0.0",
                            "model": self.model_name,
                            "capabilities": ["text_generation", "context_aware", "enhanced_context"]
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
                                # Update raw context data from sensors
                                self.raw_context_data = data.get('payload', {})
                                logger.debug("Raw context data updated")
                                
                            elif msg_type == 'llm_request':
                                # Process LLM request
                                payload = data.get('payload', {})
                                query = payload.get('query', '')
                                
                                logger.info(f"Processing LLM request: {query[:100]}...")
                                
                                # Generate response with enhanced context
                                llm_response = await self.generate_response(query, self.raw_context_data)
                                
                                # Send response back
                                await websocket.send(json.dumps({
                                    "type": "llm_response",
                                    "payload": llm_response,
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                                logger.info(f"LLM response sent: {llm_response['response'][:100]}...")
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except websockets.exceptions.ConnectionClosed as e:
                            logger.error(f"Connection closed: {e}")
                            break
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
        """Main method to run the enhanced LLM service"""
        logger.info(f"Starting Enhanced Ollama LLM service")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/enhanced_ollama_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Find available models
        await self.find_available_models()
        logger.info(f"Using model: {self.model_name}")
        
        # Initialize context connection
        context_connected = await self.initialize_context_connection()
        if not context_connected:
            logger.warning("Could not connect to enhanced context system, continuing with basic context only")
        
        # Connect to bridge server
        await self.connect_to_bridge_server()

# Function to run the enhanced LLM service
async def run_enhanced_ollama_service():
    llm = EnhancedOllamaLLM()
    await llm.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_enhanced_ollama_service())
    except KeyboardInterrupt:
        logger.info("Enhanced Ollama service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Enhanced Ollama service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)