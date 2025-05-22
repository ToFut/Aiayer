#!/usr/bin/env python3
"""
Enhanced Memory Bridge with Integrated Search Capabilities
This script provides a bridge between the client and server with its own memory search system.
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
import traceback

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedMemorySearch:
    """Simple memory system with basic search capabilities."""
    
    def __init__(self):
        """Initialize the memory system."""
        self.memories = []
        logger.info("IntegratedMemorySearch initialized")
    
    def add_memory(self, content, type="message"):
        """Add a memory item to the system."""
        try:
            # Create memory item
            memory = {
                "content": content,
                "type": type,
                "timestamp": datetime.now().isoformat(),
                "id": len(self.memories) + 1,
                "tokens": self._tokenize(content)
            }
            
            # Store memory
            self.memories.append(memory)
            
            logger.info(f"Added memory ({type}): {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def _tokenize(self, text):
        """Convert text to lowercase tokens."""
        if not isinstance(text, str):
            text = str(text)
        return re.findall(r'\w+', text.lower())
    
    def search(self, query, limit=3):
        """Search for memories matching the query."""
        try:
            if not self.memories:
                logger.warning("No memories to search")
                return []
            
            # Tokenize query
            query_tokens = self._tokenize(query)
            
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

# Global integrated memory system
memory_system = IntegratedMemorySearch()

async def bridge_messages():
    """
    Act as a message bridge between client and server.
    Intercepts messages, handles memory, and fixes formatting issues.
    """
    try:
        # Connect to the server
        logger.info("Starting enhanced memory bridge...")
        server_ws = await websockets.connect('ws://localhost:8765')
        logger.info("Connected to server on port 8765")
        
        # Start a local server for the client to connect to
        port = 8766
        logger.info(f"Starting local bridge server on port {port}")
        
        # Store client connections
        clients = set()
        
        async def handle_client(websocket, path):
            """Handle client connections and messages."""
            logger.info(f"Client connected from {websocket.remote_address}")
            clients.add(websocket)
            
            try:
                # Send initial connection message
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "status": "connected",
                        "bridged": True,
                        "memory_enabled": True,
                        "timestamp": time.time()
                    }
                }))
                
                # Handle messages from client
                async for message in websocket:
                    logger.info(f"Received from client: {message[:100]}...")
                    
                    try:
                        data = json.loads(message)
                        message_type = data.get("type", "unknown")
                        
                        # Handle different message types
                        if message_type == "user_interaction":
                            await handle_user_interaction(websocket, server_ws, data)
                        elif message_type == "memory_query":
                            await handle_memory_query(websocket, data)
                        elif message_type == "memory_clear":
                            memory_system.clear()
                            await websocket.send(json.dumps({
                                "type": "memory_cleared",
                                "payload": {
                                    "success": True,
                                    "timestamp": time.time()
                                }
                            }))
                        else:
                            # Forward other messages to the server
                            await server_ws.send(json.dumps(data))
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client: {message[:100]}...")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "error": "Invalid JSON format"
                            }
                        }))
                    except Exception as e:
                        logger.error(f"Error processing client message: {e}")
                        logger.error(traceback.format_exc())
                        
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "error": f"Error processing message: {str(e)}"
                            }
                        }))
            
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client disconnected")
            finally:
                clients.remove(websocket)
        
        async def handle_user_interaction(websocket, server_ws, data):
            """Handle user interaction messages."""
            payload = data.get("payload", {})
            
            # Check if it's a query message
            if isinstance(payload, dict) and "query" in payload:
                query = payload.get("query", "")
                
                # Add to memory system
                memory_system.add_memory(query, type="user_query")
                
                # Check if it's a memory search request
                if query.lower().startswith("search my") or "memory" in query.lower():
                    logger.info(f"Handling as memory search: {query}")
                    
                    # Perform memory search
                    results = memory_system.search(query, limit=5)
                    
                    # Format results
                    if results:
                        response_text = f"Here are the results of your memory search:\n\n"
                        for i, result in enumerate(results):
                            response_text += f"{i+1}. {result['content']}\n"
                            response_text += f"   (Relevance: {result['score']:.2f})\n\n"
                    else:
                        response_text = "I couldn't find any relevant memories matching your query."
                    
                    # Send response
                    await websocket.send(json.dumps({
                        "type": "query_response",
                        "payload": {
                            "query": query,
                            "response": response_text,
                            "timestamp": time.time()
                        }
                    }))
                    
                    # Also add the response to memory
                    memory_system.add_memory(response_text, type="assistant_response")
                    
                else:
                    # Fix the payload format if needed
                    if "type" not in payload:
                        data["payload"] = {
                            "type": "query",
                            "query": query
                        }
                    
                    # Forward to server
                    await server_ws.send(json.dumps(data))
            else:
                # Forward to server
                await server_ws.send(json.dumps(data))
        
        async def handle_memory_query(websocket, data):
            """Handle explicit memory query requests."""
            payload = data.get("payload", {})
            query = payload.get("query", "")
            limit = payload.get("limit", 5)
            
            # Perform memory search
            results = memory_system.search(query, limit=limit)
            
            # Send response
            await websocket.send(json.dumps({
                "type": "memory_query_results",
                "payload": {
                    "query": query,
                    "results": results,
                    "timestamp": time.time()
                }
            }))
        
        # Start server
        async with websockets.serve(handle_client, "localhost", port):
            logger.info(f"Enhanced memory bridge running on ws://localhost:{port}")
            
            # Listen for messages from the server
            while True:
                try:
                    # Wait for server messages
                    message = await server_ws.recv()
                    logger.info(f"Received from server: {message[:100]}...")
                    
                    # Store responses in memory
                    try:
                        data = json.loads(message)
                        if data.get("type") == "query_response":
                            payload = data.get("payload", {})
                            query = payload.get("query", "")
                            response = payload.get("response", "")
                            
                            # Store the response in memory
                            memory_system.add_memory(response, type="assistant_response")
                    except:
                        pass
                    
                    # Broadcast to all clients
                    if clients:
                        await asyncio.gather(
                            *[client.send(message) for client in clients],
                            return_exceptions=True
                        )
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Server connection closed")
                    # Try to reconnect
                    logger.info("Attempting to reconnect to server...")
                    try:
                        server_ws = await websockets.connect('ws://localhost:8765')
                        logger.info("Reconnected to server on port 8765")
                    except:
                        logger.error("Failed to reconnect to server")
                        # Wait before trying again
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error from server: {e}")
                    logger.error(traceback.format_exc())
                    continue
    
    except Exception as e:
        logger.error(f"Bridge startup error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        # Print instructions
        print("\n===== Enhanced Memory Bridge =====")
        print("This bridge provides memory and search functionality")
        print("Main server: ws://localhost:8765")
        print("Bridge server: ws://localhost:8766")
        print("Connect your client to the bridge server instead of the main server")
        print("")
        print("Special commands:")
        print("- To search memory: Send a message starting with 'Search my...'")
        print("- To clear memory: Send a message with type 'memory_clear'")
        print("=====================================\n")
        
        asyncio.run(bridge_messages())
    except KeyboardInterrupt:
        print("\nBridge stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())