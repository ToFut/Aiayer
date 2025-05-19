#!/usr/bin/env python3
"""
Test utility for the semantic search system.
This script connects to the memory bridge and tests search functionality.
"""
import asyncio
import websockets
import json
import time
import logging
import sys
import os
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_semantic_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SemanticSearchTester:
    """Client to test semantic search functionality."""
    
    def __init__(self, bridge_url="ws://localhost:8766"):
        """Initialize the tester."""
        self.bridge_url = bridge_url
        self.websocket = None
        self.connected = False
        self.message_queue = asyncio.Queue()
        
    async def connect(self):
        """Connect to the memory bridge."""
        try:
            self.websocket = await websockets.connect(self.bridge_url)
            self.connected = True
            logger.info(f"Connected to {self.bridge_url}")
            
            # Send initial connection message
            await self.websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "semantic_search_tester",
                    "version": "1.0.0",
                    "timestamp": time.time()
                }
            }))
            
            # Start listening for messages
            asyncio.create_task(self.message_listener())
            
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def message_listener(self):
        """Listen for messages from the bridge."""
        try:
            while self.connected and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                logger.info(f"Received message of type: {data.get('type')}")
                
                # Add to queue for processing
                await self.message_queue.put(data)
                
                # Process special message types
                if data.get("type") == "query_response":
                    payload = data.get("payload", {})
                    response = payload.get("response", "")
                    print(f"\n[RESPONSE] {response}\n")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            self.connected = False
    
    async def send_query(self, query):
        """Send a query to the bridge."""
        if not self.connected:
            logger.error("Not connected")
            return False
        
        try:
            # Send query
            await self.websocket.send(json.dumps({
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": query
                }
            }))
            
            logger.info(f"Sent query: {query}")
            return True
        except Exception as e:
            logger.error(f"Error sending query: {e}")
            return False
    
    async def get_stats(self):
        """Get bridge statistics."""
        if not self.connected:
            logger.error("Not connected")
            return None
        
        try:
            # Request stats
            await self.websocket.send(json.dumps({
                "type": "bridge_stats"
            }))
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                # Check if we have a response in the queue
                try:
                    data = self.message_queue.get_nowait()
                    if data.get("type") == "bridge_stats_response":
                        return data.get("payload", {}).get("stats", {})
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.1)
            
            logger.error("Timeout waiting for stats response")
            return None
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return None
    
    async def clear_memory(self):
        """Clear the memory in the bridge."""
        if not self.connected:
            logger.error("Not connected")
            return False
        
        try:
            # Send clear request
            await self.websocket.send(json.dumps({
                "type": "memory_clear"
            }))
            
            logger.info("Sent memory clear request")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False
    
    async def run_test_session(self):
        """Run a test session with predefined messages and searches."""
        if not self.connected:
            if not await self.connect():
                logger.error("Could not connect")
                return False
        
        # Clear any existing memory
        await self.clear_memory()
        print("\nMemory cleared. Starting test session...")
        
        # Send some initial messages to populate memory
        test_messages = [
            "My name is Alex and I work as a software engineer",
            "I'm currently working on a machine learning project",
            "The project involves using natural language processing for semantic search",
            "Python and TensorFlow are the main technologies we're using",
            "We need to improve the search accuracy and performance"
        ]
        
        print("\n--- Sending initial messages to populate memory ---")
        for message in test_messages:
            print(f"Sending: {message}")
            await self.send_query(message)
            await asyncio.sleep(1)
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Run some search queries
        search_queries = [
            "search for information about my name",
            "find details about the project I'm working on",
            "what technologies am I using?",
            "search for anything related to Python",
            "find all memories about search functionality"
        ]
        
        print("\n--- Testing search functionality ---")
        for query in search_queries:
            print(f"\n[QUERY] {query}")
            await self.send_query(query)
            # Wait for response
            await asyncio.sleep(2)
        
        # Get statistics
        stats = await self.get_stats()
        if stats:
            print("\n--- Bridge Statistics ---")
            for key, value in stats.items():
                print(f"{key}: {value}")
        
        print("\nTest session completed!")
        return True
    
    async def disconnect(self):
        """Disconnect from the bridge."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected")

async def interactive_mode():
    """Run in interactive mode."""
    tester = SemanticSearchTester()
    
    if not await tester.connect():
        print("Failed to connect. Make sure the memory bridge is running.")
        return
    
    print("\n=== Semantic Search Test Client ===")
    print("Connected to memory bridge!")
    print("Available commands:")
    print("  /clear - Clear memory")
    print("  /stats - Get bridge statistics")
    print("  /test - Run automated test session")
    print("  /quit - Exit program")
    print("Or type any message to send as a query")
    print("=====================================\n")
    
    try:
        while True:
            user_input = input("> ")
            
            if user_input.lower() == "/quit":
                break
            elif user_input.lower() == "/clear":
                await tester.clear_memory()
                print("Memory cleared")
            elif user_input.lower() == "/stats":
                stats = await tester.get_stats()
                if stats:
                    print("\n--- Bridge Statistics ---")
                    for key, value in stats.items():
                        print(f"{key}: {value}")
                    print("")
                else:
                    print("Failed to get statistics")
            elif user_input.lower() == "/test":
                await tester.run_test_session()
            else:
                await tester.send_query(user_input)
                # Wait briefly for response
                await asyncio.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        await tester.disconnect()

async def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated test
        tester = SemanticSearchTester()
        if await tester.connect():
            await tester.run_test_session()
            await tester.disconnect()
    else:
        # Run interactive mode
        await interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Error: {e}")
        sys.exit(1)