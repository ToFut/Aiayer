#!/usr/bin/env python3
"""
Memory Test WebSocket Server

This server provides a WebSocket interface for testing memory system functionality.
It allows sending messages to test memory storage and retrieval, and shows exactly
what's happening in the semantic search process.
"""

import asyncio
import json
import logging
import time
import traceback
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import websockets
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory_test_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_test")

# Import memory system components
try:
    from memory.semantic_search_agent import search_memories, add_memory, get_context_for_query
    # Removed dependency on update_memory_state
    MEMORY_SYSTEM_AVAILABLE = True
    logger.info("Memory system modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import memory system: {e}")
    MEMORY_SYSTEM_AVAILABLE = False

# Connection management
connected_clients = set()
client_info = {}

# Keep track of search history
search_history = []
MAX_SEARCH_HISTORY = 100

async def handle_websocket(websocket, path=None):
    """Handle WebSocket connections and messages"""
    client_id = str(uuid.uuid4())
    connected_clients.add(websocket)
    client_info[websocket] = {
        "id": client_id,
        "connected_at": datetime.now().isoformat(),
        "ip": websocket.remote_address[0] if hasattr(websocket, "remote_address") else "unknown",
        "request_count": 0
    }
    
    logger.info(f"Client connected: {client_id} from {client_info[websocket]['ip']}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "memory_system_available": MEMORY_SYSTEM_AVAILABLE,
            "server_time": datetime.now().isoformat(),
            "client_id": client_id
        }))
        
        # Handle messages
        async for message in websocket:
            await process_message(websocket, message)
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {client_id} - Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        logger.error(f"Error handling WebSocket: {e}")
        logger.error(traceback.format_exc())
    finally:
        connected_clients.remove(websocket)
        if websocket in client_info:
            del client_info[websocket]

async def process_message(websocket, message):
    """Process incoming WebSocket messages"""
    try:
        # Update request stats
        if websocket in client_info:
            client_info[websocket]["request_count"] += 1
        
        data = json.loads(message)
        message_type = data.get("type", "unknown")
        
        logger.info(f"Received message: {message_type}")
        
        # Process based on message type
        if message_type == "ping":
            await handle_ping(websocket, data)
        elif message_type == "add_memory":
            await handle_add_memory(websocket, data)
        elif message_type == "search_memory":
            await handle_search_memory(websocket, data)
        elif message_type == "get_system_stats":
            await handle_get_system_stats(websocket, data)
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }))
    
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON: {message}")
        await websocket.send(json.dumps({
            "type": "error",
            "error": "Invalid JSON message"
        }))
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        logger.error(traceback.format_exc())
        await websocket.send(json.dumps({
            "type": "error",
            "error": str(e)
        }))

async def handle_ping(websocket, data):
    """Handle ping messages"""
    await websocket.send(json.dumps({
        "type": "pong",
        "timestamp": datetime.now().isoformat(),
        "memory_system_available": MEMORY_SYSTEM_AVAILABLE
    }))

async def handle_add_memory(websocket, data):
    """Handle add memory requests"""
    if not MEMORY_SYSTEM_AVAILABLE:
        await websocket.send(json.dumps({
            "type": "error",
            "error": "Memory system not available"
        }))
        return
    
    try:
        content = data.get("content", "").strip()
        source = data.get("source", "user")
        tags = set(data.get("tags", []))
        metadata = data.get("metadata", {})
        
        if not content:
            raise ValueError("Memory content is required")
        
        # Process the memory details
        memory_processing = {
            "original_content": content,
            "processed_content": content,  # In a real system, this might be normalized/tokenized
            "source": source,
            "tags": list(tags),
            "metadata": metadata,
            "processing_time_ms": 0
        }
        
        # Add memory with timing
        start_time = time.time()
        # Pass the arguments as keyword arguments to avoid positional argument error
        success = await add_memory(content=content, source=source, tags=tags, metadata=metadata)
        end_time = time.time()
        processing_time_ms = round((end_time - start_time) * 1000, 2)
        
        memory_processing["processing_time_ms"] = processing_time_ms
        
        # Send response
        await websocket.send(json.dumps({
            "type": "memory_added",
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "memory_id": str(uuid.uuid4()),  # In a real system, this would be the actual ID
            "memory_processing": memory_processing
        }))
        
        logger.info(f"Memory added: {success} in {processing_time_ms}ms")
        
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "error": f"Failed to add memory: {str(e)}"
        }))

async def handle_search_memory(websocket, data):
    """Handle memory search requests"""
    if not MEMORY_SYSTEM_AVAILABLE:
        await websocket.send(json.dumps({
            "type": "error",
            "error": "Memory system not available"
        }))
        return
    
    try:
        # Extract search parameters
        query = data.get("query", "").strip()
        top_k = int(data.get("top_k", 5))
        min_similarity = float(data.get("min_similarity", 0.1))
        source_filter = data.get("source_filter")
        application_context = data.get("application_context")
        
        if not query:
            raise ValueError("Search query is required")
        
        # Prepare search process details
        search_process = {
            "original_query": query,
            "processed_query": query,  # In a real system, this might be normalized
            "parameters": {
                "top_k": top_k,
                "min_similarity": min_similarity,
                "source_filter": source_filter,
                "application_context": application_context
            },
            "search_strategy": "vector_similarity",  # In a real system, this might vary
            "total_search_time_ms": 0,
            "embedding_time_ms": 0,
            "retrieval_time_ms": 0,
            "ranking_time_ms": 0
        }
        
        # Perform search with timing
        search_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Simulate embedding time (in a real system, this would be the actual embedding calculation)
        embedding_start = time.time()
        await asyncio.sleep(0.05)  # Simulate embedding computation
        embedding_time = time.time() - embedding_start
        search_process["embedding_time_ms"] = round(embedding_time * 1000, 2)
        
        # Perform the actual search
        retrieval_start = time.time()
        search_results = await search_memories(
            query=query,
            top_k=top_k,
            source_filter=source_filter,
            min_similarity=min_similarity,
            application_context=application_context
        )
        retrieval_time = time.time() - retrieval_start
        search_process["retrieval_time_ms"] = round(retrieval_time * 1000, 2)
        
        # Convert SearchResult objects to dictionaries for JSON serialization
        results = []
        for result in search_results:
            # Create a serializable dictionary from the SearchResult object
            result_dict = {
                "content": result.content,
                "similarity_score": float(result.similarity_score),
                "source": result.source,
                "timestamp": result.timestamp.isoformat(),
                "metadata": result.metadata,
                "context": result.context,
                "confidence": float(result.confidence),
                "relevance_factors": result.relevance_factors
            }
            results.append(result_dict)
        
        # Simulate ranking/post-processing time
        ranking_start = time.time()
        await asyncio.sleep(0.02)  # Simulate ranking computation
        ranking_time = time.time() - ranking_start
        search_process["ranking_time_ms"] = round(ranking_time * 1000, 2)
        
        end_time = time.time()
        total_search_time_ms = round((end_time - start_time) * 1000, 2)
        search_process["total_search_time_ms"] = total_search_time_ms
        
        # Add to search history
        search_history.append({
            "id": search_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(results),
            "search_time_ms": total_search_time_ms
        })
        if len(search_history) > MAX_SEARCH_HISTORY:
            search_history.pop(0)
        
        # Get related memory concepts for visualization
        # In a real system, this would identify the key topics and concepts from the memory
        related_concepts = await extract_related_concepts(query, results)
        
        # Send response
        await websocket.send(json.dumps({
            "type": "search_results",
            "search_id": search_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "result_count": len(results),
            "search_process": search_process,
            "related_concepts": related_concepts
        }))
        
        logger.info(f"Memory search: '{query}' found {len(results)} results in {total_search_time_ms}ms")
        
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        logger.error(traceback.format_exc())
        await websocket.send(json.dumps({
            "type": "error",
            "error": f"Failed to search memory: {str(e)}"
        }))

async def extract_related_concepts(query, results):
    """Extract related concepts from search results for visualization"""
    try:
        # This is a simplified version - in a real system, this would be more sophisticated
        concepts = []
        
        # Extract potential concepts from the query
        query_words = query.lower().split()
        query_concepts = [word for word in query_words if len(word) > 3]
        
        # Add query concepts
        for concept in query_concepts:
            concepts.append({
                "name": concept,
                "type": "query",
                "weight": 1.0,
                "connections": []
            })
        
        # Extract concepts from results
        result_concepts = {}
        for i, result in enumerate(results):
            # Now result is a dictionary, not a SearchResult object
            content = result.get("content", "")
            words = content.lower().split()
            
            for word in words:
                if len(word) > 3 and word not in query_words:
                    if word not in result_concepts:
                        result_concepts[word] = {
                            "count": 0,
                            "documents": set(),
                            "connections": []
                        }
                    
                    result_concepts[word]["count"] += 1
                    result_concepts[word]["documents"].add(i)
                    
                    # Connect to query concepts
                    for qc in query_concepts:
                        result_concepts[word]["connections"].append(qc)
        
        # Convert to list format and add connections
        for word, data in result_concepts.items():
            if data["count"] >= 2:  # Only include words that appear multiple times
                concepts.append({
                    "name": word,
                    "type": "result",
                    "weight": min(1.0, data["count"] / 10),  # Normalize weight
                    "connections": data["connections"]
                })
        
        return concepts
    
    except Exception as e:
        logger.error(f"Error extracting concepts: {e}")
        return []

async def handle_get_system_stats(websocket, data):
    """Handle requests for system statistics"""
    if not MEMORY_SYSTEM_AVAILABLE:
        await websocket.send(json.dumps({
            "type": "system_stats",
            "memory_system_available": False,
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    try:
        # In a real system, these would be actual counts from the memory system
        memory_stats = {
            "total_memories": 0,
            "short_term_count": 0,
            "long_term_count": 0,
            "search_stats": {
                "total_searches": len(search_history),
                "avg_search_time_ms": 0,
                "successful_searches": 0
            }
        }
        
        # Calculate average search time
        if search_history:
            avg_time = sum(item["search_time_ms"] for item in search_history) / len(search_history)
            memory_stats["search_stats"]["avg_search_time_ms"] = round(avg_time, 2)
            memory_stats["search_stats"]["successful_searches"] = sum(1 for item in search_history if item["result_count"] > 0)
        
        # Try to get actual memory counts if possible
        try:
            # This assumes there's a memory_state.json file with counts
            memory_state_path = os.path.join('memory', 'memory_state.json')
            if os.path.exists(memory_state_path):
                with open(memory_state_path, 'r') as f:
                    memory_state = json.load(f)
                    
                    # Extract counts from memory state
                    if isinstance(memory_state, dict):
                        # Handle updated memory state format with short_term and long_term arrays
                        short_term_memories = memory_state.get("short_term", [])
                        long_term_memories = memory_state.get("long_term", [])
                        
                        memory_stats["total_memories"] = len(short_term_memories) + len(long_term_memories)
                        memory_stats["short_term_count"] = len(short_term_memories)
                        memory_stats["long_term_count"] = len(long_term_memories)
                        
                        logger.info(f"Memory counts - Total: {memory_stats['total_memories']}, Short-term: {memory_stats['short_term_count']}, Long-term: {memory_stats['long_term_count']}")
        except Exception as e:
            logger.warning(f"Error reading memory state: {e}")
        
        # Send response
        await websocket.send(json.dumps({
            "type": "system_stats",
            "memory_system_available": True,
            "timestamp": datetime.now().isoformat(),
            "stats": memory_stats,
            "search_history": search_history[-10:]  # Send last 10 searches
        }))
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "error": f"Failed to get system stats: {str(e)}"
        }))

async def main():
    """Start the WebSocket server"""
    try:
        host = "localhost"
        port = 8769
        
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Create the server
        logger.info(f"Starting WebSocket server on ws://{host}:{port}")
        async with websockets.serve(handle_websocket, host, port):
            print(f"Memory Test WebSocket Server running at ws://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            
            # Keep the server running indefinitely
            await asyncio.Future()
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())