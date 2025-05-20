#!/usr/bin/env python3
"""
Agent-Based WebSocket Server with LLM Integration
Implements a comprehensive WebSocket server that connects clients, memory systems, 
and LLM services with advanced semantic search and perception query handling.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import aiohttp
import importlib.util
import traceback
import numpy as np
from datetime import datetime
import pkg_resources

# Check if scikit-learn is installed, if not, install it
try:
    pkg_resources.get_distribution('scikit-learn')
except pkg_resources.DistributionNotFound:
    import subprocess
    print("Installing scikit-learn...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])

# Import scikit-learn components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
os.makedirs('logs', exist_ok=True)
# Remove all handlers associated with the root logger object (to avoid duplicate logs)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aiayer.log'),
        logging.StreamHandler()
    ]
)
# Ensure all loggers propagate to the root logger
logging.getLogger('agent').propagate = True
logging.getLogger('agent_based_llm').propagate = True
logging.getLogger('memory_system').propagate = True
logging.getLogger('memory_diagnostics').propagate = True
logger = logging.getLogger('agent_based_llm')

# WebSocket clients
connected_clients = set()
client_info = {}  # Store client info by ID

# Global components
memory_system = None
ollama_service = None

class OllamaService:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3"  # Default model, will try to find best available
        
    async def list_models(self):
        """List available models from Ollama API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        models = await resp.json()
                        logger.info(f"Available Ollama models: {models}")
                        
                        # Find a model to use
                        if models and "models" in models and models["models"]:
                            # Try to find a good model or default to first available
                            for model in models["models"]:
                                # Prefer llama3 models
                                if "llama3" in model["name"].lower():
                                    self.model_name = model["name"]
                                    logger.info(f"Using model: {self.model_name}")
                                    return True
                                # Fallback to any llama model
                                elif "llama" in model["name"].lower():
                                    self.model_name = model["name"]
                                    logger.info(f"Using model: {self.model_name}")
                                    return True
                            
                            # If no preferred model found, use first available
                            self.model_name = models["models"][0]["name"]
                            logger.info(f"Using model: {self.model_name}")
                            return True
                        
                        logger.warning("No Ollama models found")
                        return False
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return False
        
    async def generate_response(self, prompt):
        """Generate a response using Ollama API"""
        try:
            logger.info(f"Generating response with prompt length: {len(prompt)}")
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                start_time = datetime.now()
                logger.info(f"Calling Ollama API at {self.ollama_url}/api/generate")
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Ollama API error: {resp.status} - {error_text}")
                        return {
                            "response": f"Error generating response: {resp.status} - {error_text}",
                            "model": self.model_name,
                            "error": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    result = await resp.json()
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Generated response in {processing_time:.2f}s")
                    logger.info(f"Response: {result.get('response', '')[:100]}...")
                    
                    return {
                        "response": result.get("response", "No response generated"),
                        "model": self.model_name,
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": f"Sorry, I encountered an error while generating a response: {str(e)}",
                "model": self.model_name,
                "error": True,
                "timestamp": datetime.now().isoformat()
            }

class Agent:
    """Intelligent agent that mediates between clients, memory, and LLM"""
    
    def __init__(self, memory_system=None, llm_service=None):
        self.memory_system = memory_system
        self.llm_service = llm_service
        self.logger = logging.getLogger('agent')
        self.conversation_history = []  # Maintain local conversation history
        
        # Initialize TF-IDF vectorizer for semantic search
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer='word',
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        self.memory_vectors = None
        self.memory_texts = []
        self.memory_items = []
        
    async def process_message(self, user_message, client_id=None):
        """Process a user message, collect context, and generate a response"""
        self.logger.info("==================================================")
        self.logger.info("🤖 AGENT MESSAGE PROCESSING STARTED")
        self.logger.info(f"📨 Message from client {client_id}: {user_message[:100]}...")
        self.logger.info("==================================================")
        
        try:
            # 1. Store user message in conversation history and memory system
            self.logger.info("📝 STEP 1: Storing user message...")
            timestamp = datetime.now().isoformat()
            message_data = {
                "type": "user_message", 
                "content": user_message,
                "client_id": client_id,
                "timestamp": timestamp
            }
            
            self.conversation_history.append(message_data)
            self.logger.info("✅ Added message to local conversation history")
            
            # Store in memory system if available
            if self.memory_system:
                try:
                    await self.memory_system.add_message(message_data)
                    self.logger.info("✅ Stored user message in memory system")
                except Exception as e:
                    self.logger.error(f"❌ Error storing message in memory: {e}")
                    self.logger.error(traceback.format_exc())
            else:
                self.logger.warning("⚠️ No memory system available for storing message")
            
            # 2. Collect relevant context from memory system
            self.logger.info("🧠 STEP 2: Collecting relevant context...")
            start_time = datetime.now()
            context = await self.collect_context(user_message)
            context_time = (datetime.now() - start_time).total_seconds()
            
            if context:
                self.logger.info(f"✅ Context collected in {context_time:.2f}s with {len(context)} elements")
                # Log details of collected context
                self.logger.info("📊 Context Details:")
                for key, value in context.items():
                    if isinstance(value, (str, list, dict)):
                        preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        self.logger.info(f"  - {key}: {preview}")
            else:
                self.logger.warning(f"⚠️ No context collected after {context_time:.2f}s")
            
            # 3. Construct prompt for LLM with context
            self.logger.info("📋 STEP 3: Constructing LLM prompt...")
            start_time = datetime.now()
            prompt = await self.construct_prompt(user_message, context)
            prompt_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"✅ Prompt constructed in {prompt_time:.2f}s ({len(prompt)} chars)")
            self.logger.info("📝 Prompt Preview:")
            self.logger.info(f"{prompt[:500]}...")
            
            # 4. Generate response using LLM service
            self.logger.info("🧩 STEP 4: Generating LLM response...")
            start_time = datetime.now()
            
            if self.llm_service:
                self.logger.info(f"📲 Sending prompt to LLM service ({self.llm_service.model_name})")
                response_data = await self.llm_service.generate_response(prompt)
                response_text = response_data.get("response", "")
                llm_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"✅ LLM response generated in {llm_time:.2f}s ({len(response_text)} chars)")
                self.logger.info(f"📤 Response: {response_text[:100]}...")
            else:
                self.logger.error("❌ No LLM service available")
                response_text = "Agent could not connect to LLM service to generate a response."
                response_data = {
                    "response": response_text,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 5. Store response in conversation history and memory system
            self.logger.info("💾 STEP 5: Storing response...")
            response_message = {
                "type": "assistant_message",
                "content": response_text,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.conversation_history.append(response_message)
            self.logger.info("✅ Added response to local conversation history")
            
            # Store in memory system if available
            if self.memory_system:
                try:
                    await self.memory_system.add_message(response_message)
                    self.logger.info("✅ Stored assistant response in memory system")
                except Exception as e:
                    self.logger.error(f"❌ Error storing response in memory: {e}")
                    self.logger.error(traceback.format_exc())
            
            # 6. Return response data
            self.logger.info("==================================================")
            self.logger.info("🎉 AGENT PROCESSING COMPLETE")
            self.logger.info("==================================================")
            
            return {
                **response_data,
                "context_used": bool(context),
                "context_keys": list(context.keys()) if context else [],
                "agent_processed": True,
                "processing_info": {
                    "context_time_seconds": context_time,
                    "prompt_time_seconds": prompt_time,
                    "prompt_length": len(prompt),
                    "response_length": len(response_text)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ ERROR IN AGENT PROCESSING: {e}")
            self.logger.error(traceback.format_exc())
            self.logger.info("==================================================")
            self.logger.info("❌ AGENT PROCESSING FAILED")
            self.logger.info("==================================================")
            
            return {
                "response": f"The agent encountered an error while processing your message: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def collect_context(self, user_message):
        """Collect relevant context from memory system"""
        context = {}
        
        self.logger.info("========== CONTEXT COLLECTION START ==========")
        self.logger.info(f"Collecting context for message: {user_message[:50]}...")
        
        if not self.memory_system:
            self.logger.warning("❌ No memory system available for context collection")
            return context
        
        try:
            # Check if this is a perception-related query
            perception_patterns = [
                "what am i seeing", "what do i see", "what's on my screen",
                "what is on my screen", "what's being displayed", "what is displayed",
                "what's in front of me", "what is in front of me", "what's visible",
                "what around me", "what do you see", "what are you seeing"
            ]
            
            is_perception_query = any(pattern in user_message.lower() for pattern in perception_patterns)
            if is_perception_query:
                self.logger.info("👁️ Perception query detected, prioritizing visual context")
            
            # 1. Get current environment context
            self.logger.info("📑 STEP 1: Retrieving environment context summary...")
            try:
                context_summary = await self.memory_system.get_context_summary()
                context_size = len(str(context_summary))
                self.logger.info(f"✅ Successfully retrieved context summary ({context_size} chars)")
                
                # Log what's in the context
                if 'window' in context_summary:
                    self.logger.info(f"  - Active window: {context_summary['window']}")
                if 'active_apps' in context_summary:
                    self.logger.info(f"  - Active apps: {len(context_summary.get('active_apps', []))} apps")
                if 'screen_content' in context_summary:
                    screen_len = len(context_summary.get('screen_content', ''))
                    self.logger.info(f"  - Screen content: {screen_len} chars")
                
                context = context_summary
            except Exception as e:
                self.logger.error(f"❌ Error getting context summary: {e}")
                self.logger.error(traceback.format_exc())
            
            # 2. Search for relevant memories related to the user's query
            self.logger.info("🔍 STEP 2: Searching for relevant memories...")
            try:
                # For perception queries, we want to search for visual/screen content
                if is_perception_query:
                    self.logger.info("👁️ Performing specialized search for perception query")
                    search_query = "screen content visual display window active"
                    relevant_memories = await self.search_memory(search_query, limit=5)
                else:
                    relevant_memories = await self.search_memory(user_message, limit=5)
                
                if relevant_memories:
                    self.logger.info(f"✅ Found {len(relevant_memories)} relevant memories")
                    for i, memory in enumerate(relevant_memories):
                        if isinstance(memory, dict):
                            content = memory.get('content', '')[:50]
                            source = memory.get('source', 'unknown')
                            self.logger.info(f"  - Memory {i+1}: [{source}] {content}...")
                    context['relevant_memories'] = relevant_memories
                else:
                    self.logger.info("⚠️ No relevant memories found")
            except Exception as e:
                self.logger.error(f"❌ Error searching memory: {e}")
                self.logger.error(traceback.format_exc())
            
            # 3. Get recent conversation history
            self.logger.info("💬 STEP 3: Retrieving recent conversation history...")
            try:
                recent_messages = self.get_recent_messages(count=5)
                if recent_messages:
                    self.logger.info(f"✅ Retrieved {len(recent_messages)} recent messages")
                    for i, msg in enumerate(recent_messages):
                        if isinstance(msg, dict):
                            msg_type = msg.get('type', 'unknown')
                            content = msg.get('content', '')[:50]
                            self.logger.info(f"  - Message {i+1}: [{msg_type}] {content}...")
                    context['recent_messages'] = recent_messages
                else:
                    self.logger.info("⚠️ No recent messages found in memory system")
                    # Fallback to local conversation history
                    if self.conversation_history:
                        self.logger.info(f"  - Using {len(self.conversation_history[-5:])} messages from local history")
                        context['recent_messages'] = self.conversation_history[-5:]
            except Exception as e:
                self.logger.error(f"❌ Error getting recent messages: {e}")
                self.logger.error(traceback.format_exc())
                # Fallback to local conversation history
                if self.conversation_history:
                    self.logger.info(f"  - Using {len(self.conversation_history[-5:])} messages from local history after error")
                    context['recent_messages'] = self.conversation_history[-5:] if len(self.conversation_history) > 0 else []
            
            self.logger.info(f"========== CONTEXT COLLECTION COMPLETE ==========")
            self.logger.info(f"Final context contains {len(context)} keys: {list(context.keys())}")
            return context
            
        except Exception as e:
            self.logger.error(f"❌ ERROR in collect_context: {e}")
            self.logger.error(traceback.format_exc())
            self.logger.info("========== CONTEXT COLLECTION FAILED ==========")
            return {}
    
    def get_recent_messages(self, count=5):
        """Get recent messages from conversation history"""
        try:
            # First try to get messages from memory system
            if self.memory_system and hasattr(self.memory_system, 'get_recent_messages'):
                try:
                    messages = self.memory_system.get_recent_messages(count=count)
                    if messages and len(messages) > 0:
                        return messages
                except Exception as e:
                    self.logger.error(f"Error getting messages from memory system: {e}")
            
            # Fallback to local conversation history
            return self.conversation_history[-count:] if len(self.conversation_history) >= count else self.conversation_history
        except Exception as e:
            self.logger.error(f"Error in get_recent_messages: {e}")
            return []
    
    async def construct_prompt(self, user_message, context):
        """Construct an optimized prompt for the LLM with relevant context"""
        self.logger.info("========== PROMPT CONSTRUCTION START ==========")
        
        try:
            # Start with a system message
            system_message = "You are a helpful assistant with access to the user's environment context.\n\n"
            
            # Include relevant context information
            if context:
                self.logger.info(f"✅ Using context with {len(context)} keys: {list(context.keys())}")
                
                # Add active window and application if available
                if 'window' in context:
                    window = context.get('window', 'Unknown')
                    system_message += f"Active Window: {window}\n"
                    self.logger.info(f"  - Added active window: {window}")
                    
                if 'active_apps' in context:
                    apps = context.get('active_apps', [])
                    if apps:
                        apps_str = ', '.join(apps)
                        system_message += f"Active Applications: {apps_str}\n"
                        self.logger.info(f"  - Added {len(apps)} active applications")
                
                # Add screen content if available
                if 'screen_content' in context and context['screen_content']:
                    screen_content = context['screen_content']
                    system_message += f"\nScreen Content:\n{screen_content}\n"
                    self.logger.info(f"  - Added screen content: {len(screen_content)} chars")
                
                # Add recent files if available
                if 'recent_files' in context:
                    files = context.get('recent_files', [])
                    if files:
                        files_str = '\n'.join(f"- {f}" for f in files)
                        system_message += f"\nRecent Files:\n{files_str}\n"
                        self.logger.info(f"  - Added {len(files)} recent files")
                
                # Add current file if available
                if 'current_file' in context:
                    current_file = context.get('current_file')
                    if current_file:
                        system_message += f"\nCurrent File: {current_file}\n"
                        self.logger.info(f"  - Added current file: {current_file}")
                
                # Add conversation history if available
                if 'recent_messages' in context and context['recent_messages']:
                    messages = context['recent_messages']
                    self.logger.info(f"  - Adding {len(messages)} recent messages to context")
                    
                    system_message += "\nRecent Conversation:\n"
                    message_count = 0
                    
                    for msg in messages:
                        if isinstance(msg, dict):
                            role = "User" if msg.get('type') == 'user_message' else "Assistant"
                            content = msg.get('content', '')
                            if content:
                                system_message += f"{role}: {content}\n"
                                message_count += 1
                                
                    self.logger.info(f"  - Successfully added {message_count} conversation messages")
                
                # Add relevant memories if available
                if 'relevant_memories' in context and context['relevant_memories']:
                    memories = context['relevant_memories']
                    self.logger.info(f"  - Adding {len(memories)} relevant memories to context")
                    
                    system_message += "\nRelevant Context From Memory:\n"
                    memory_count = 0
                    
                    for memory in memories:
                        if isinstance(memory, dict) and 'content' in memory:
                            system_message += f"- {memory['content']}\n"
                            memory_count += 1
                            
                    self.logger.info(f"  - Successfully added {memory_count} memory entries")
            else:
                self.logger.warning("⚠️ No context available, using basic prompt")
            
            # Add user's current message
            self.logger.info(f"📤 Adding user message: {user_message[:50]}...")
            full_prompt = f"{system_message}\n\nUser: {user_message}\n\nAssistant:"
            
            prompt_length = len(full_prompt)
            self.logger.info(f"✅ Constructed prompt with {prompt_length} chars")
            
            # Log token estimation (rough approximation)
            token_estimate = prompt_length / 4  # ~4 chars per token
            self.logger.info(f"📊 Estimated tokens: ~{int(token_estimate)}")
            
            self.logger.info("========== PROMPT CONSTRUCTION COMPLETE ==========")
            return full_prompt
            
        except Exception as e:
            self.logger.error(f"❌ ERROR constructing prompt: {e}")
            self.logger.error(traceback.format_exc())
            self.logger.info("========== PROMPT CONSTRUCTION FAILED ==========")
            
            # Fallback to simple prompt
            fallback_prompt = f"User: {user_message}\nAssistant:"
            self.logger.info(f"⚠️ Using fallback prompt: {len(fallback_prompt)} chars")
            return fallback_prompt
    
    async def process_sensor_data(self, sensor_type, sensor_data):
        """Process and store sensor data in memory system"""
        if not self.memory_system:
            self.logger.warning(f"No memory system available to process {sensor_type} sensor data")
            return False
        
        try:
            await self.memory_system.process_sensor_data(sensor_type, sensor_data)
            self.logger.info(f"Processed {sensor_type} sensor data")
            return True
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            return False
    
    async def update_memory_vectors(self):
        """Update the vector representations of all memory items"""
        try:
            self.logger.info("🔄 Updating memory vectors with TF-IDF...")
            
            if not self.memory_system:
                self.logger.warning("⚠️ No memory system available for vectorization")
                return False
                
            # Get all available memory
            all_memory = []
            
            # Add short-term memory
            if hasattr(self.memory_system, 'short_term_memory'):
                short_term = self.memory_system.short_term_memory
                self.logger.info(f"Retrieved {len(short_term)} short-term memory items")
                all_memory.extend([(item, 'short_term') for item in short_term])
            
            # Add long-term memory
            if hasattr(self.memory_system, 'long_term_memory'):
                long_term = self.memory_system.long_term_memory
                self.logger.info(f"Retrieved {len(long_term)} long-term memory items")
                all_memory.extend([(item, 'long_term') for item in long_term])
            
            # Add context memory items
            if hasattr(self.memory_system, 'context_memory'):
                if isinstance(self.memory_system.context_memory, dict):
                    context_items = []
                    
                    # Check for searchable items
                    if 'searchable_items' in self.memory_system.context_memory:
                        searchable = self.memory_system.context_memory['searchable_items']
                        if isinstance(searchable, dict):
                            for key, item in searchable.items():
                                context_items.append((item, 'context'))
                                
                    # Also add other context items
                    for key, value in self.memory_system.context_memory.items():
                        if key != 'searchable_items' and isinstance(value, dict):
                            context_items.append((value, 'context'))
                    
                    self.logger.info(f"Retrieved {len(context_items)} context memory items")
                    all_memory.extend(context_items)
            
            # Extract text from memory items
            self.memory_texts = []
            self.memory_items = []
            
            for item, source in all_memory:
                if isinstance(item, dict):
                    # First try to get text directly from the item
                    text = None
                    
                    if 'text' in item:
                        text = item['text']
                    elif 'content' in item:
                        text = item['content']
                    elif 'message_content' in item:
                        text = item['message_content']
                    elif 'screen_content' in item:
                        text = item['screen_content']
                    
                    # If we found text, add it to our collection
                    if text and isinstance(text, str):
                        self.memory_texts.append(text)
                        self.memory_items.append({'item': item, 'source': source})
            
            # Create vector representations if we have enough texts
            if len(self.memory_texts) > 0:
                self.memory_vectors = self.vectorizer.fit_transform(self.memory_texts)
                self.logger.info(f"✅ Created vector representations for {len(self.memory_texts)} memory items")
                self.logger.info(f"📊 Vector dimensions: {self.memory_vectors.shape}")
                return True
            else:
                self.logger.warning("⚠️ No text found in memory items for vectorization")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error updating memory vectors: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    async def semantic_search(self, query, limit=5):
        """Search memory using semantic similarity with scikit-learn"""
        try:
            self.logger.info(f"🔍 Performing semantic search for: {query[:50]}...")
            
            # Update vectors if needed
            if self.memory_vectors is None or len(self.memory_texts) == 0:
                self.logger.info("Memory vectors not initialized, updating now...")
                success = await self.update_memory_vectors()
                if not success:
                    self.logger.warning("Unable to create memory vectors, falling back to basic search")
                    # Fall back to standard memory search
                    return await self.memory_system.search_memory(query, limit) if self.memory_system else []
            
            # Check if this is a perception-related query (about what user is seeing)
            perception_patterns = [
                "what am i seeing", "what do i see", "what's on my screen",
                "what is on my screen", "what's being displayed", "what is displayed",
                "what's in front of me", "what is in front of me", "what's visible",
                "what around me", "what do you see", "what are you seeing"
            ]
            
            is_perception_query = any(pattern in query.lower() for pattern in perception_patterns)
            
            if is_perception_query:
                self.logger.info("👁️ Detected perception-related query, prioritizing screen/visual data")
                
                # Modify the query to focus on screen content and visual data
                enhanced_query = f"{query} screen content visual display window active app"
                query_vector = self.vectorizer.transform([enhanced_query])
            else:
                # Regular query
                query_vector = self.vectorizer.transform([query])
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(query_vector, self.memory_vectors).flatten()
            
            # If this is a perception query, adjust the scores to prioritize visual content
            if is_perception_query:
                visual_weights = np.ones(similarity_scores.shape)
                for i, text in enumerate(self.memory_texts):
                    text_lower = text.lower()
                    # Give more weight to screen-related memories
                    if "screen" in text_lower or "window" in text_lower or "display" in text_lower:
                        visual_weights[i] = 2.0
                        self.logger.info(f"  - Boosting visual content: {text[:30]}...")
                
                # Apply weights to the similarity scores
                similarity_scores = similarity_scores * visual_weights
            
            # Sort by similarity
            sorted_indices = similarity_scores.argsort()[::-1]
            
            # Get top results
            results = []
            top_indices = sorted_indices[:limit]
            
            self.logger.info(f"🎯 Found {len(top_indices)} results with semantic search")
            
            for idx in top_indices:
                score = similarity_scores[idx]
                if score > 0.1:  # Minimum similarity threshold
                    item = self.memory_items[idx]['item']
                    source = self.memory_items[idx]['source']
                    text = self.memory_texts[idx]
                    
                    result = {
                        'content': text,
                        'score': float(score),
                        'source': source,
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'original_item': item
                    }
                    
                    results.append(result)
                    self.logger.info(f"  - Result {len(results)}: [score={score:.2f}] {text[:50]}...")
                    
            # Log if we handled a perception query
            if is_perception_query:
                self.logger.info("👁️ Handled perception query with enhanced semantic search")
                    
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in semantic search: {e}")
            self.logger.error(traceback.format_exc())
            # Fall back to standard memory search
            self.logger.info("Falling back to standard memory search")
            return await self.memory_system.search_memory(query, limit) if self.memory_system else []
    
    async def search_memory(self, query, limit=5):
        """Search memory for relevant information, using enhanced semantic search"""
        if not self.memory_system:
            self.logger.warning("No memory system available for search")
            return []
        
        try:
            # First try semantic search with scikit-learn
            semantic_results = await self.semantic_search(query, limit)
            
            if semantic_results:
                self.logger.info(f"✅ Semantic search for '{query}' returned {len(semantic_results)} results")
                return semantic_results
            
            # Fall back to basic search if semantic search fails or returns no results
            self.logger.info("No semantic search results, falling back to basic search")
            results = await self.memory_system.search_memory(query, limit)
            self.logger.info(f"✅ Basic memory search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error searching memory: {e}")
            self.logger.error(traceback.format_exc())
            return []

# Initialize agent
agent = None

# Extract message from different payload formats
def extract_message(data):
    """Extract the user message from different possible data formats"""
    if 'payload' in data and isinstance(data['payload'], dict):
        return data['payload'].get('message', data['payload'].get('query', ''))
    elif 'message' in data:
        return data['message']
    elif 'query' in data:
        return data['query']
    elif 'content' in data:
        return data['content']
    return ""

async def initialize_memory_system():
    """Initialize the memory system for context-aware responses"""
    try:
        logger.info("Initializing memory system...")
        
        # Dynamically import memory system
        spec = importlib.util.spec_from_file_location(
            "memory_system", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                         "memory/memory_system.py")
        )
        memory_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(memory_module)
        
        # Initialize the memory system
        memory_system = memory_module.MemorySystem()
        await memory_system.initialize()
        
        logger.info("Memory system initialized successfully")
        return memory_system
    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        logger.error(traceback.format_exc())
        return None

# WebSocket handler
async def websocket_handler(websocket):
    """Handle WebSocket connections and messages."""
    try:
        # Add client to connected clients
        connected_clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(connected_clients)}")
        
        # Send initial connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "message": "Connected to AIayer server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                logger.info(f"Received message: {data}")
                
                # Extract message type and content
                msg_type = data.get('type', '')
                payload = data.get('payload', {})
                
                # Handle different message types
                if msg_type == 'sensor_data':
                    # Process sensor data
                    sensor_type = payload.get('sensor_type')
                    sensor_data = payload.get('data', {})
                    if sensor_type and sensor_data:
                        await memory_system.process_sensor_data(sensor_type, sensor_data)
                        logger.info(f"Processed {sensor_type} sensor data")
                
                elif msg_type == 'message':
                    # Process regular message
                    message_content = payload.get('content', '')
                    if message_content:
                        response = await agent.process_message(message_content)
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "content": response,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    else:
                        logger.warning("No message content found in data: %s", data)
                
                elif msg_type == 'llm_request':
                    # Process LLM request
                    request_content = payload.get('content', '')
                    if request_content:
                        response = await agent.process_message(request_content)
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "content": response,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    else:
                        logger.warning("No request content found in data: %s", data)
                
                elif msg_type == 'chat_message':
                    # Process chat message
                    message_content = payload.get('content', '')
                    if message_content:
                        response = await agent.process_message(message_content)
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "content": response,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    else:
                        logger.warning("No chat message content found in data: %s", data)
                
                elif msg_type == 'context_request':
                    # Handle context request
                    request_id = payload.get('requestId')
                    if request_id:
                        # Get current context from memory system
                        context = await memory_system.get_context_summary()
                        
                        # Add request ID to response
                        context['requestId'] = request_id
                        
                        # Send context response
                        await websocket.send(json.dumps({
                            "type": "context_response",
                            "payload": {
                                "context": context,
                                "requestId": request_id,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        logger.info(f"Sent context response for request {request_id}")
                    else:
                        logger.warning("No request ID found in context request: %s", data)
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": f"Unknown message type: {msg_type}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": f"Error processing message: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove client from connected clients
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Remaining clients: {len(connected_clients)}")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                # Get agent and memory stats if available
                agent_stats = {
                    "active": agent is not None,
                    "memory_active": agent.memory_system is not None if agent else False,
                    "conversation_length": len(agent.conversation_history) if agent else 0
                }
                
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients),
                    "agent": agent_stats
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def periodic_vector_update():
    """Periodically updates the vector representations of memory items"""
    global agent
    
    if not agent:
        logger.warning("No agent available for vector updates")
        return
        
    while True:
        try:
            logger.info("🔄 Running periodic memory vector update...")
            await agent.update_memory_vectors()
            logger.info("✅ Memory vectors updated successfully")
        except Exception as e:
            logger.error(f"❌ Error in periodic vector update: {e}")
        
        # Update every 5 minutes
        await asyncio.sleep(300)

async def main():
    global agent, ollama_service
    
    # Initialize ollama service
    logger.info("Initializing Ollama service...")
    ollama_service = OllamaService()
    ollama_initialized = await ollama_service.list_models()
    if not ollama_initialized:
        logger.warning("Failed to initialize Ollama service, will continue without LLM capabilities")
        ollama_service = None
    
    # Initialize memory system
    logger.info("Initializing Memory system...")
    memory_system = await initialize_memory_system()
    if not memory_system:
        logger.warning("Memory system initialization failed, agent will have limited capabilities")
    
    # Initialize agent
    logger.info("Initializing Agent...")
    agent = Agent(memory_system=memory_system, llm_service=ollama_service)
    logger.info("Agent initialized successfully")
    
    # Initialize the agent's vector representations
    logger.info("Building initial memory vectors...")
    await agent.update_memory_vectors()
    
    # Set up WebSocket server
    port = 8765
    host = "0.0.0.0"  # Listen on all interfaces
    
    # Create directories
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Start background tasks
        heartbeat_task = asyncio.create_task(heartbeat())
        vector_update_task = asyncio.create_task(periodic_vector_update())
        
        # Start the WebSocket server
        async with websockets.serve(
            websocket_handler,
            host,
            port,
            ping_interval=30,
            ping_timeout=10
        ):
            # Save PID
            with open('pids/agent_based_llm_ws.pid', 'w') as f:
                f.write(str(os.getpid()))
                
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            logger.info(f"Using LLM model: {ollama_service.model_name if ollama_service else 'None'}")
            logger.info(f"Agent: {'ACTIVE' if agent else 'INACTIVE'}")
            logger.info(f"Memory system: {'ACTIVE' if memory_system else 'INACTIVE'}")
            logger.info(f"Vector search: ENABLED")
            
            # Keep running forever
            await asyncio.Future()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        # Clean up memory system
        if memory_system:
            try:
                await memory_system.cleanup()
                logger.info("Memory system cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up memory system: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)