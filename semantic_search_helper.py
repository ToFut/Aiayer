#!/usr/bin/env python3
"""
Semantic Search Helper for Overlay System

Simple tool to help with semantic search functionality 
without requiring external models or complex dependencies.
"""
import asyncio
import websockets
import json
import time
import logging
import os
import re
from collections import Counter
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/semantic_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleSemanticSearch:
    """Simple semantic search implementation for overlay system."""
    
    def __init__(self):
        """Initialize the semantic search."""
        self.memories = []
        self.max_memories = 50  # Maximum number of memories to store
        logger.info("SimpleSemanticSearch initialized")
    
    def add_memory(self, content, type="message", metadata=None):
        """Add a memory item."""
        try:
            # Create memory item
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
        """Search for memories matching the query."""
        try:
            if not self.memories:
                logger.warning("No memories to search")
                return []
            
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
                
                scored_memories.append((memory, normalized_score))
            
            # Sort by score
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            
            # Get top results
            results = []
            for memory, score in scored_memories[:limit]:
                result = memory.copy()
                del result["tokens"]  # Remove tokens from result
                result["score"] = score
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        logger.info("Memory cleared")
        return True

# Global search instance
search = SimpleSemanticSearch()

# WebSocket client class
class OverlayClient:
    """Client to connect to WebSocket server and handle memory search."""
    
    def __init__(self, url="ws://localhost:8765"):
        """Initialize the client."""
        self.url = url
        self.connected = False
        self.ws = None
        logger.info(f"OverlayClient initialized with URL: {url}")
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.ws = await websockets.connect(self.url)
            self.connected = True
            logger.info(f"Connected to server: {self.url}")
            
            # Send initial connection message
            await self.ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "semantic_search_helper",
                    "version": "1.0.0",
                    "timestamp": time.time()
                }
            }))
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info("Disconnected from server")
    
    async def listen(self):
        """Listen for messages from the server."""
        if not self.connected or not self.ws:
            logger.error("Cannot listen: not connected")
            return
        
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self.process_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
    
    async def process_message(self, data):
        """Process a message from the server."""
        try:
            message_type = data.get("type", "unknown")
            
            # Handle different message types
            if message_type == "query_response":
                # Store assistant responses in memory
                payload = data.get("payload", {})
                query = payload.get("query", "")
                response = payload.get("response", "")
                
                if response:
                    search.add_memory(response, type="assistant_response", metadata={
                        "source_query": query,
                        "timestamp": payload.get("timestamp", datetime.now().isoformat())
                    })
                    logger.info(f"Stored assistant response in memory")
            
            elif message_type == "user_interaction":
                # Store user queries in memory
                payload = data.get("payload", {})
                if isinstance(payload, dict) and "query" in payload:
                    query = payload.get("query", "")
                    
                    if query:
                        search.add_memory(query, type="user_query", metadata={
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.info(f"Stored user query in memory: {query[:50]}...")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def send_query(self, query, handle_response=False):
        """Send a query to the server."""
        if not self.connected or not self.ws:
            logger.error("Cannot send query: not connected")
            return None
        
        try:
            message = {
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": query
                }
            }
            
            await self.ws.send(json.dumps(message))
            logger.info(f"Sent query: {query[:50]}...")
            
            # Optionally wait for response
            if handle_response:
                response = await self.ws.recv()
                return json.loads(response)
            
            return True
        except Exception as e:
            logger.error(f"Error sending query: {e}")
            return None
    
    async def search_memory(self, query, limit=5):
        """Search memory and return results."""
        results = search.search(query, limit)
        return results
    
    async def run_search_cli(self):
        """Run an interactive CLI for semantic search."""
        print("\n=== Semantic Search Helper ===")
        print("Type 'quit' to exit, 'clear' to clear memory")
        print("Type 'search <query>' to search memory")
        print("Type 'add <message>' to add to memory")
        print("Or just type a message to send as a query to the server")
        print("===============================\n")
        
        while True:
            try:
                cmd = input("> ")
                
                if cmd.lower() == "quit":
                    break
                elif cmd.lower() == "clear":
                    search.clear()
                    print("Memory cleared")
                elif cmd.lower().startswith("search "):
                    query = cmd[7:]  # Remove "search " prefix
                    results = search.search(query)
                    
                    if results:
                        print(f"\nFound {len(results)} results for: {query}")
                        for i, result in enumerate(results):
                            print(f"\n{i+1}. [{result['type']}] {result['content']}")
                            print(f"   Score: {result['score']:.4f}")
                    else:
                        print(f"No results found for: {query}")
                elif cmd.lower().startswith("add "):
                    message = cmd[4:]  # Remove "add " prefix
                    search.add_memory(message)
                    print(f"Added to memory: {message[:50]}...")
                else:
                    # Send as query to server
                    print(f"Sending query: {cmd}")
                    await self.send_query(cmd)
                    print("Query sent")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nExiting search CLI")

async def main():
    """Main function."""
    try:
        # Initialize client
        url = "ws://localhost:8765"  # Default URL
        client = OverlayClient(url)
        
        # Connect to server
        if not await client.connect():
            logger.error(f"Could not connect to server at {url}")
            return
        
        # Start listening in a separate task
        listener_task = asyncio.create_task(client.listen())
        
        # Run CLI
        await client.run_search_cli()
        
        # Disconnect
        await client.disconnect()
        
        # Cancel listener task
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    print("\nStarting Semantic Search Helper...")
    print("This tool helps with semantic search for the overlay system")
    print("It connects to the backend server and builds a searchable memory")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")