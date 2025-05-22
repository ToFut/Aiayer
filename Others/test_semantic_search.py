#!/usr/bin/env python3
"""
Test Semantic Search Functionality
This script tests the semantic search functionality of the backend server
"""
import asyncio
import websockets
import json
import time
import logging
import os
import random

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/semantic_search_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_semantic_search():
    """Test the semantic search functionality of the memory system."""
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
                    "capabilities": ["memory", "context", "notification"],
                    "timestamp": time.time()
                }
            }))
            
            # Read initial response
            response = await websocket.recv()
            logger.info(f"Initial response: {response}")
            
            # Step 1: Add some test messages to the memory system
            logger.info("Step 1: Adding test messages to memory...")
            messages = [
                "Python is a high-level programming language with dynamic typing",
                "Machine learning is a subset of artificial intelligence that uses data to learn",
                "The weather today is sunny with a high of 75 degrees",
                "I need to remember to buy groceries this weekend",
                "WebSockets provide a persistent connection between a client and server"
            ]
            
            for i, message in enumerate(messages):
                await websocket.send(json.dumps({
                    "type": "user_interaction",
                    "payload": {
                        "type": "query",
                        "query": message
                    }
                }))
                
                # Wait for response
                response = await websocket.recv()
                logger.info(f"Message {i+1} response received")
                
                # Short delay between messages
                await asyncio.sleep(1)
            
            # Step 2: Test semantic search with related queries
            logger.info("Step 2: Testing semantic search...")
            search_queries = [
                "Tell me about programming languages",
                "What is artificial intelligence?",
                "What's the weather like?",
                "What should I do this weekend?",
                "How do WebSockets work?"
            ]
            
            print("\n=== SEMANTIC SEARCH TEST RESULTS ===\n")
            for i, query in enumerate(search_queries):
                # Perform a memory search
                await websocket.send(json.dumps({
                    "type": "memory_query",
                    "payload": {
                        "query": query,
                        "limit": 3
                    }
                }))
                
                try:
                    # Wait for response with a timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    # Check if it's a memory query response
                    if response_data.get("type") == "memory_query_results":
                        print(f"Query: {query}")
                        results = response_data.get("payload", {}).get("results", [])
                        
                        if results:
                            print(f"Found {len(results)} relevant memories:")
                            for j, result in enumerate(results):
                                print(f"  {j+1}. Content: {result.get('content', 'N/A')}")
                                print(f"     Score: {result.get('score', 'N/A')}")
                                print()
                        else:
                            print("No relevant memories found\n")
                    else:
                        # If we get a different response type, continue waiting
                        print(f"Received non-memory response: {response_data.get('type')}")
                        
                        # Try one more time with a direct query
                        await websocket.send(json.dumps({
                            "type": "user_interaction",
                            "payload": {
                                "type": "query",
                                "query": f"Search my memory for information about: {query}"
                            }
                        }))
                        
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"Interactive search response received")
                        
                except asyncio.TimeoutError:
                    print(f"Timeout waiting for response to query: {query}\n")
                
                # Delay between queries
                await asyncio.sleep(2)
            
            print("\n=== TEST COMPLETED ===\n")
            
            # Extra: Test with some completely random queries to verify
            logger.info("Testing with random queries...")
            random_queries = [
                "quantum computing applications",
                "best recipe for chocolate chip cookies",
                "history of ancient Egypt",
                "how to optimize python code"
            ]
            
            random_query = random.choice(random_queries)
            await websocket.send(json.dumps({
                "type": "memory_query",
                "payload": {
                    "query": random_query,
                    "limit": 3
                }
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Random query response received: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.info(f"Timeout waiting for random query response")
            
            logger.info("Test completed")
            
            # Get final status
            await websocket.send(json.dumps({
                "type": "status_request",
                "payload": {
                    "timestamp": time.time()
                }
            }))
            
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                status_data = json.loads(status_response)
                
                if status_data.get("type") == "status_response":
                    print("Server Status:")
                    print(f"  Memory System Active: {status_data.get('payload', {}).get('memory_system_active')}")
                    print(f"  Advanced LLM Initialized: {status_data.get('payload', {}).get('advanced_llm_initialized')}")
                    print(f"  LLM Model: {status_data.get('payload', {}).get('llm_model')}")
                    print(f"  Connected Clients: {status_data.get('payload', {}).get('connected_clients')}")
                
            except (asyncio.TimeoutError, json.JSONDecodeError):
                print("Could not retrieve server status")
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        print(f"Error in test: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_semantic_search())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")