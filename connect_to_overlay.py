#!/usr/bin/env python3
"""
Connect to Overlay with Enhanced Search

This script helps connect to the overlay system with enhanced search capabilities.
It's a simplified version that ensures proper message formatting and search functionality.
"""
import asyncio
import websockets
import json
import time
import logging
import os
import re
from datetime import datetime
from collections import Counter

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Simple memory system for search
memories = []
MAX_MEMORIES = 50

def add_memory(content, type="message"):
    """Add a memory to the system."""
    global memories
    
    memory = {
        "content": content,
        "type": type,
        "timestamp": datetime.now().isoformat(),
        "id": len(memories) + 1
    }
    
    memories.append(memory)
    
    # Limit number of memories
    if len(memories) > MAX_MEMORIES:
        memories = memories[-MAX_MEMORIES:]
    
    logger.info(f"Added {type} memory: {content[:50]}...")
    return True

def search_memories(query, limit=5):
    """Search memories using simple token matching."""
    global memories
    
    if not memories:
        return []
    
    # Tokenize query and memories
    query_tokens = set(re.findall(r'\w+', query.lower()))
    
    # Score each memory based on token overlap
    scored_memories = []
    for memory in memories:
        memory_tokens = set(re.findall(r'\w+', memory["content"].lower()))
        
        # Calculate overlap
        common_tokens = query_tokens.intersection(memory_tokens)
        score = len(common_tokens) / max(len(query_tokens), 1)
        
        if score > 0:
            scored_memories.append((memory, score))
    
    # Sort by score
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    
    # Return top results
    results = []
    for memory, score in scored_memories[:limit]:
        result = memory.copy()
        result["score"] = score
        results.append(result)
    
    return results

async def connect_to_overlay(server_url="ws://localhost:8765"):
    """Connect to the overlay WebSocket server."""
    try:
        logger.info(f"Connecting to overlay server at {server_url}")
        
        while True:
            try:
                async with websockets.connect(server_url) as websocket:
                    logger.info("Connected to overlay server")
                    
                    # Send registration message
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "application",
                        "version": "1.0.0",
                        "capabilities": ["search", "memory"],
                        "timestamp": time.time()
                    }))
                    
                    # Start listener for incoming messages
                    await handle_messages(websocket)
            
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.error(f"Connection error: {e}")
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Reconnecting in 10 seconds...")
                await asyncio.sleep(10)
    
    except asyncio.CancelledError:
        logger.info("Connection task cancelled")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

async def handle_messages(websocket):
    """Handle messages from the WebSocket server."""
    while True:
        try:
            # Receive message from server
            message = await websocket.recv()
            data = json.loads(message)
            
            message_type = data.get("type", "unknown")
            logger.info(f"Received message of type: {message_type}")
            
            # Process different message types
            if message_type == "user_interaction":
                await handle_user_interaction(websocket, data)
            elif message_type == "query_response":
                await handle_response(websocket, data)
            elif message_type == "memory_query":
                await handle_memory_query(websocket, data)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
            break
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

async def handle_user_interaction(websocket, data):
    """Handle user interaction messages."""
    payload = data.get("payload", {})
    
    # Check if it's a query
    if isinstance(payload, dict) and "query" in payload:
        query = payload.get("query", "")
        
        # Add to memory
        add_memory(query, "user_query")
        
        # Check if it's a search request
        if "search" in query.lower() or "find" in query.lower() or "look for" in query.lower():
            # Perform search
            results = search_memories(query, limit=5)
            
            # Format search results
            if results:
                response_text = f"I found the following in memory:\n\n"
                for i, result in enumerate(results):
                    response_text += f"{i+1}. {result['content']}\n"
                    response_text += f"   Relevance: {result['score']:.2f}\n\n"
            else:
                response_text = "I couldn't find anything relevant in memory."
            
            # Send back search response
            await websocket.send(json.dumps({
                "type": "query_response",
                "payload": {
                    "query": query,
                    "response": response_text,
                    "timestamp": time.time()
                }
            }))
            
            # Store the response in memory
            add_memory(response_text, "assistant_response")
            
            return True
    
    # If not handled, pass it on unchanged
    return False

async def handle_response(websocket, data):
    """Handle responses from the server."""
    payload = data.get("payload", {})
    
    if isinstance(payload, dict):
        query = payload.get("query", "")
        response = payload.get("response", "")
        
        # Store in memory
        if response:
            add_memory(response, "assistant_response")
            logger.info(f"Stored assistant response in memory")
    
    return True

async def handle_memory_query(websocket, data):
    """Handle direct memory query requests."""
    payload = data.get("payload", {})
    
    if isinstance(payload, dict):
        query = payload.get("query", "")
        limit = payload.get("limit", 5)
        
        # Perform search
        results = search_memories(query, limit)
        
        # Send results
        await websocket.send(json.dumps({
            "type": "memory_query_results",
            "payload": {
                "query": query,
                "results": results,
                "timestamp": time.time()
            }
        }))
        
        logger.info(f"Sent memory query results for: {query}")
        return True
    
    return False

async def main():
    """Main entry point."""
    try:
        # Try connecting to both possible WebSocket URLs
        server_tasks = []
        
        # First try the bridge URL (8766)
        server_tasks.append(asyncio.create_task(
            connect_to_overlay("ws://localhost:8766")
        ))
        
        # Then try the direct URL (8765)
        server_tasks.append(asyncio.create_task(
            connect_to_overlay("ws://localhost:8765")
        ))
        
        # Wait for any task to complete (they'll all be in reconnect loops)
        done, pending = await asyncio.wait(
            server_tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel any remaining tasks
        for task in pending:
            task.cancel()
    
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    print("\n=== Overlay Connector with Enhanced Search ===")
    print("Connecting to overlay WebSocket server...")
    print("This connector provides enhanced search capabilities")
    print("It automatically stores messages and allows searching them")
    print("\nPress Ctrl+C to stop")
    print("=====================================\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")