#!/usr/bin/env python3
"""
Fixed Semantic Search Test
Correctly formats search queries to test memory and semantic search
"""
import asyncio
import websockets
import json
import time
import logging
import os
import random
import traceback

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_semantic_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def fixed_semantic_search():
    """Test the semantic search with properly formatted requests."""
    try:
        # Connect to the server
        logger.info("Connecting to the server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            logger.info("Connected to server")
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "version": "1.0.0",
                    "capabilities": ["memory", "context", "search"],
                    "timestamp": time.time()
                }
            }))
            
            # Read initial response
            response = await websocket.recv()
            logger.info(f"Initial response: {response[:100]}...")
            
            # Step 1: Add some test messages to build up the memory
            print("\n=== ADDING TEST MESSAGES TO MEMORY ===\n")
            
            messages = [
                "Python is a high-level programming language with dynamic typing",
                "Machine learning models require large amounts of training data",
                "WebSockets provide real-time communication between client and server",
                "I need to remember to buy groceries this weekend",
                "The memory system uses semantic search for retrieving relevant information"
            ]
            
            # Send messages to build up the memory
            for i, message in enumerate(messages):
                print(f"Adding message {i+1}: {message}")
                
                await websocket.send(json.dumps({
                    "type": "user_interaction",
                    "payload": {
                        "type": "query",
                        "query": message
                    }
                }))
                
                # Wait for response (but don't process it)
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    print(f"√ Response received for message {i+1}")
                except asyncio.TimeoutError:
                    print(f"× Timeout waiting for response to message {i+1}")
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            # Step 2: Test search using direct queries that trigger semantic search
            print("\n=== TESTING SEMANTIC SEARCH WITH DIRECT QUERIES ===\n")
            
            search_queries = [
                "Tell me about programming",
                "What is machine learning?",
                "How do WebSockets work?",
                "What do I need to do this weekend?",
                "How does the memory system work?"
            ]
            
            for i, query in enumerate(search_queries):
                print(f"\nQuery {i+1}: \"{query}\"")
                
                # Format a query that explicitly requests memory search
                formatted_query = f"Search my previous messages for: {query}"
                print(f"Sending formatted query: \"{formatted_query}\"")
                
                await websocket.send(json.dumps({
                    "type": "user_interaction",
                    "payload": {
                        "type": "query",
                        "query": formatted_query
                    }
                }))
                
                # Wait for response with timeout
                try:
                    # We need to read multiple responses as the server might send status updates
                    start_time = time.time()
                    response_received = False
                    
                    while time.time() - start_time < 10.0 and not response_received:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            response_data = json.loads(response)
                            
                            # Check if it's a query response
                            if response_data.get("type") == "query_response":
                                print(f"✓ Received response:")
                                response_text = response_data.get("payload", {}).get("response", "")
                                
                                # Print a formatted version of the response
                                if len(response_text) > 500:
                                    print(f"{response_text[:500]}... (truncated)")
                                else:
                                    print(response_text)
                                
                                response_received = True
                                break
                            else:
                                # Skip non-query responses (like status updates)
                                logger.info(f"Received non-query response: {response_data.get('type')}")
                        
                        except asyncio.TimeoutError:
                            # This is fine, we'll keep trying within our overall timeout
                            logger.info("Timeout waiting for individual response")
                    
                    if not response_received:
                        print("× No valid response received within timeout")
                        
                except Exception as e:
                    print(f"× Error processing response: {e}")
                    logger.error(f"Error processing response: {e}")
                    logger.error(traceback.format_exc())
                
                # Delay between queries
                await asyncio.sleep(2)
            
            # Final status check
            print("\n=== SERVER STATUS ===\n")
            
            await websocket.send(json.dumps({
                "type": "status_request",
                "payload": {
                    "timestamp": time.time()
                }
            }))
            
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                status_data = json.loads(status_response)
                
                if status_data.get("type") == "status_response" or status_data.get("type") == "status_update":
                    payload = status_data.get("payload", status_data.get("data", {}))
                    print("Server Status:")
                    print(f"  Memory System Active: {payload.get('memory_system_active', 'Unknown')}")
                    print(f"  Advanced LLM Initialized: {payload.get('advanced_llm_initialized', 'Unknown')}")
                    print(f"  LLM Model: {payload.get('llm_model', 'Unknown')}")
                    print(f"  Connected Clients: {payload.get('client_count', 'Unknown')}")
                    
                    # Report on memory metrics if available
                    memory_metrics = payload.get("memory_system", {})
                    if memory_metrics:
                        print("\nMemory Metrics:")
                        for key, value in memory_metrics.items():
                            print(f"  {key}: {value}")
                else:
                    print(f"Received non-status response: {status_data.get('type')}")
            except (asyncio.TimeoutError, json.JSONDecodeError) as e:
                print(f"Could not retrieve server status: {e}")
            
            print("\n=== TEST COMPLETED ===\n")
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        logger.error(traceback.format_exc())
        print(f"Error in test: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(fixed_semantic_search())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())