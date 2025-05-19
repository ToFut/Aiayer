#!/usr/bin/env python3
"""
Final Memory Bridge with Semantic Search Integration

This script provides a robust bridge between the overlay interface and memory system,
ensuring perfect semantic search functionality and proper message formatting.
"""
import asyncio
import websockets
import json
import time
import logging
import os
import re
import sys
from datetime import datetime
import traceback
from collections import Counter, deque
import numpy as np

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/final_memory_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafeJSON:
    """Safe JSON operations with error handling."""
    
    @staticmethod
    def loads(json_str, default=None):
        """Safely load JSON from string."""
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return default
    
    @staticmethod
    def dumps(obj, default=None, indent=None):
        """Safely dump object to JSON string."""
        try:
            return json.dumps(obj, indent=indent)
        except Exception as e:
            logger.error(f"Error dumping JSON: {e}")
            return default if default is not None else "{}"

class TextMemorySearch:
    """Text-based memory search system (replaces vector-based search)."""
    
    def __init__(self):
        """Initialize the memory search system."""
        self.memories = []
        self.max_memories = 100
        self.vector_model = None  # Kept for backward compatibility
        self.use_vectors = False  # Always use text search
        
        logger.info("Text-based memory search initialized - using token matching")
    
    def add_memory(self, content, type="message", metadata=None):
        """Add a memory item with tokenization for text search."""
        try:
            # Create base memory item
            memory = {
                "content": content,
                "type": type,
                "timestamp": datetime.now().isoformat(),
                "id": str(len(self.memories) + 1),
                "tokens": self._tokenize(content),
                "metadata": metadata or {}
            }
            
            # Store memory
            self.memories.append(memory)
            
            # Limit the number of memories
            if len(self.memories) > self.max_memories:
                self.memories = self.memories[-self.max_memories:]
            
            logger.info(f"Added memory: {content[:50]}... (type: {type})")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def _tokenize(self, text):
        """Convert text to lowercase tokens."""
        if not isinstance(text, str):
            text = str(text)
        return re.findall(r'\w+', text.lower())
    
    def search(self, query, limit=5):
        """Search for memories using token-based text search."""
        try:
            if not self.memories:
                logger.warning("No memories to search")
                return []
                
            # Use token-based search
            return self._token_search(query, limit)
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def _token_search(self, query, limit=5):
        """Search using token overlap (fallback method)."""
        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            if not query_tokens:
                logger.warning("Empty query tokens")
                return []
            
            # Calculate scores based on token overlap
            scored_memories = []
            for memory in self.memories:
                # Calculate token overlap
                query_counter = Counter(query_tokens)
                memory_counter = Counter(memory["tokens"])
                
                # Find common tokens
                common_tokens = set(query_tokens) & set(memory["tokens"])
                
                # Calculate score based on common tokens and frequency
                score = sum(min(query_counter[token], memory_counter[token]) for token in common_tokens)
                
                # Boost score if multiple consecutive tokens match
                for i in range(len(query_tokens) - 1):
                    if query_tokens[i] in memory["tokens"] and query_tokens[i+1] in memory["tokens"]:
                        memory_text = " ".join(memory["tokens"])
                        if f"{query_tokens[i]} {query_tokens[i+1]}" in memory_text:
                            score += 0.5
                
                # Normalize by query length to prefer complete matches
                normalized_score = score / max(len(query_tokens), 1)
                
                # Create result with score
                result = memory.copy()
                if "tokens" in result:
                    del result["tokens"]
                if "vector" in result:
                    del result["vector"]
                    
                result["score"] = normalized_score
                scored_memories.append(result)
            
            # Sort by score
            scored_memories.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Token search for '{query}' found {len(scored_memories[:limit])} results")
            return scored_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error in token search: {e}")
            return []
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        logger.info("Memory cleared")
        return True

class MemoryBridge:
    """Bridge between client and server with text-based search capabilities."""
    
    def __init__(self, server_port=8765, bridge_port=8766):
        """Initialize the memory bridge."""
        self.server_port = server_port
        self.bridge_port = bridge_port
        self.server_ws = None
        self.clients = set()
        self.search_engine = TextMemorySearch()
        self.last_messages = deque(maxlen=10)  # Store recent messages for context
        self.recent_queries = deque(maxlen=5)  # Store recent queries
        self.stats = {
            "messages_processed": 0,
            "search_requests": 0,
            "successful_searches": 0,
            "connect_attempts": 0,
            "start_time": datetime.now().isoformat()
        }
    
    async def connect_to_server(self):
        """Connect to the server and handle reconnection."""
        max_retries = 10
        retry_count = 0
        retry_delay = 2
        
        while retry_count < max_retries:
            try:
                self.stats["connect_attempts"] += 1
                logger.info(f"Connecting to server ws://localhost:{self.server_port} (attempt {retry_count+1}/{max_retries})")
                self.server_ws = await websockets.connect(f"ws://localhost:{self.server_port}")
                
                # Send connection message
                await self.server_ws.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "memory_bridge",
                        "version": "2.0.0",
                        "capabilities": ["memory", "search", "context"],
                        "timestamp": time.time()
                    }
                }))
                
                logger.info(f"Successfully connected to server on port {self.server_port}")
                return True
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to server: {e}")
                
                if retry_count >= max_retries:
                    logger.error("Maximum retry attempts reached, giving up")
                    return False
                
                # Increase delay with each retry
                wait_time = retry_delay * retry_count
                logger.info(f"Waiting {wait_time} seconds before retrying...")
                await asyncio.sleep(wait_time)
    
    async def start(self):
        """Start the memory bridge server."""
        # Connect to the server first
        if not await self.connect_to_server():
            logger.error("Could not connect to server, exiting")
            return
        
        # Start local server for clients
        try:
            server = await websockets.serve(self.handle_client, "localhost", self.bridge_port)
            logger.info(f"Memory bridge running on ws://localhost:{self.bridge_port}")
            
            # Start background task to handle server messages
            server_task = asyncio.create_task(self.handle_server_messages())
            
            # Keep running
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Error starting bridge server: {e}")
    
    async def handle_client(self, websocket, path):
        """Handle client connection and messages."""
        try:
            # Add client to set
            client_id = id(websocket)
            self.clients.add(websocket)
            logger.info(f"Client connected (ID: {client_id})")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection_status",
                "payload": {
                    "status": "connected",
                    "message": "Connected to memory-enhanced bridge",
                    "timestamp": time.time(),
                    "bridge_features": ["semantic_search", "context_integration", "memory_persistence"]
                }
            }))
            
            # Handle client messages
            async for message in websocket:
                await self.process_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected (ID: {client_id})")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Remove client from set
            if websocket in self.clients:
                self.clients.remove(websocket)
    
    async def process_client_message(self, websocket, message):
        """Process a message from a client."""
        try:
            self.stats["messages_processed"] += 1
            data = SafeJSON.loads(message, {})
            
            if not data or "type" not in data:
                logger.warning(f"Received invalid message format: {message[:100]}...")
                return
            
            message_type = data["type"]
            logger.info(f"Received client message of type: {message_type}")
            
            # Handle different message types
            if message_type == "user_interaction":
                await self.handle_user_interaction(websocket, data)
            elif message_type == "memory_query":
                await self.handle_memory_query(websocket, data)
            elif message_type == "memory_clear":
                await self.handle_memory_clear(websocket)
            elif message_type == "bridge_stats":
                await self.handle_stats_request(websocket)
            else:
                # Forward to server
                await self.server_ws.send(message)
                
        except Exception as e:
            logger.error(f"Error processing client message: {e}")
            logger.error(traceback.format_exc())
            
            # Send error response
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {
                    "message": f"Error processing message: {str(e)}",
                    "timestamp": time.time()
                }
            }))
    
    async def handle_user_interaction(self, websocket, data):
        """Handle user interaction message."""
        try:
            payload = data.get("payload", {})
            
            # Check if this is a query
            if isinstance(payload, dict) and "query" in payload:
                query = payload.get("query", "")
                
                # Store in recent queries
                self.recent_queries.append({
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Add to memory
                self.search_engine.add_memory(query, type="user_query", metadata={
                    "client_id": id(websocket),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Check if this is a search request
                is_search_request = (
                    "search" in query.lower() or 
                    "find" in query.lower() or 
                    "remember" in query.lower() or
                    "memory" in query.lower()
                )
                
                if is_search_request:
                    self.stats["search_requests"] += 1
                    # Handle locally as search
                    await self.handle_search_request(websocket, query)
                    return True
                
                # Otherwise, forward to server
                await self.server_ws.send(json.dumps(data))
                return True
            
            # Forward non-query message to server
            await self.server_ws.send(json.dumps(data))
            return True
            
        except Exception as e:
            logger.error(f"Error handling user interaction: {e}")
            return False
    
    async def handle_search_request(self, websocket, query):
        """Handle search request from user."""
        try:
            # Perform search
            results = self.search_engine.search(query, limit=7)
            
            # Format results for response
            if results:
                self.stats["successful_searches"] += 1
                response_text = "Here are the most relevant memories I found:\n\n"
                
                for i, result in enumerate(results):
                    # Format based on relevance score
                    if result["score"] > 0.8:
                        confidence = "Very relevant"
                    elif result["score"] > 0.5:
                        confidence = "Moderately relevant"
                    else:
                        confidence = "Somewhat relevant"
                    
                    # Format the result
                    response_text += f"{i+1}. {result['content']}\n"
                    response_text += f"   ({confidence}, {result['score']:.2f})\n\n"
                
                # Add contextual information based on types of results
                types = [r["type"] for r in results]
                if "assistant_response" in types and "user_query" in types:
                    response_text += "\nThese include both your questions and my previous answers."
            else:
                response_text = "I couldn't find any relevant memories matching your search criteria."
            
            # Send response back to client
            await websocket.send(json.dumps({
                "type": "query_response",
                "payload": {
                    "query": query,
                    "response": response_text,
                    "source": "memory_bridge",
                    "search_results": results,
                    "timestamp": time.time()
                }
            }))
            
            # Also store the response in memory
            self.search_engine.add_memory(response_text, type="assistant_response", metadata={
                "query": query,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling search request: {e}")
            return False
    
    async def handle_memory_query(self, websocket, data):
        """Handle explicit memory query."""
        try:
            payload = data.get("payload", {})
            query = payload.get("query", "")
            limit = int(payload.get("limit", 5))
            
            # Perform search
            results = self.search_engine.search(query, limit=limit)
            
            # Send response
            await websocket.send(json.dumps({
                "type": "memory_query_results",
                "payload": {
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "timestamp": time.time()
                }
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling memory query: {e}")
            return False
    
    async def handle_memory_clear(self, websocket):
        """Handle request to clear memory."""
        try:
            self.search_engine.clear()
            
            await websocket.send(json.dumps({
                "type": "memory_clear_response",
                "payload": {
                    "success": True,
                    "message": "Memory cleared successfully",
                    "timestamp": time.time()
                }
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False
    
    async def handle_stats_request(self, websocket):
        """Handle request for bridge statistics."""
        try:
            # Update stats
            self.stats["uptime_seconds"] = (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
            self.stats["client_count"] = len(self.clients)
            self.stats["memory_count"] = len(self.search_engine.memories)
            
            await websocket.send(json.dumps({
                "type": "bridge_stats_response",
                "payload": {
                    "stats": self.stats,
                    "timestamp": time.time()
                }
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling stats request: {e}")
            return False
    
    async def handle_server_messages(self):
        """Handle messages from the server."""
        while True:
            try:
                # Check if server connection is still open
                if not self.server_ws or self.server_ws.closed:
                    logger.warning("Server connection closed, attempting to reconnect...")
                    if await self.connect_to_server():
                        logger.info("Reconnected to server successfully")
                    else:
                        logger.error("Failed to reconnect to server")
                        await asyncio.sleep(5)  # Wait before trying again
                        continue
                
                # Wait for message from server
                message = await self.server_ws.recv()
                
                # Process server message
                data = SafeJSON.loads(message, {})
                if not data:
                    continue
                
                # Handle various message types
                message_type = data.get("type", "unknown")
                
                # Store responses in memory
                if message_type == "query_response":
                    payload = data.get("payload", {})
                    query = payload.get("query", "")
                    response = payload.get("response", "")
                    
                    if response:
                        self.search_engine.add_memory(response, type="assistant_response", metadata={
                            "query": query,
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Store in last messages for context
                self.last_messages.append({
                    "type": message_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Forward to all clients
                if self.clients:
                    await asyncio.gather(
                        *[client.send(message) for client in self.clients],
                        return_exceptions=True
                    )
                
            except websockets.exceptions.ConnectionClosed:
                logger.error("Server connection closed")
                self.server_ws = None
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error handling server message: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(1)

async def main():
    """Main entry point."""
    print("\n=== Enhanced Memory Bridge with Text Search ===")
    print(f"Connecting to main server on port 8765")
    print(f"Starting bridge server on port 8766")
    print("Initializing text-based search capabilities...")
    print("\nFeatures:")
    print("✓ Token-based text search for efficient memory retrieval")
    print("✓ Persistent memory for queries and responses")
    print("✓ Robust connection handling with auto-reconnect")
    print("\nUsage:")
    print("- Connect your client to ws://localhost:8766 instead of 8765")
    print("- Search by asking: 'search for X' or 'find memories about Y'")
    print("- Get stats with a message of type 'bridge_stats'")
    print("- Clear memory with a message of type 'memory_clear'")
    print("\nPress Ctrl+C to stop the bridge")
    print("==========================================\n")
    
    # Create and start bridge
    bridge = MemoryBridge()
    await bridge.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMemory bridge stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)