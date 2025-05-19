#!/usr/bin/env python3
"""
Direct Memory Search Test

This script directly tests the memory search functionality
by implementing a simple memory system with vector search.
"""
import os
import json
import time
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory_search_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleMemorySystem:
    """A simplified memory system with vector search capabilities."""
    
    def __init__(self):
        """Initialize the memory system."""
        try:
            # Load the sentence transformer model
            logger.info("Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
            
            # Initialize memory storage
            self.memories = []
            self.vectors = []
            
            # Log initialization success
            logger.info("SimpleMemorySystem initialized successfully")
            print("Memory system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            print(f"Error initializing memory system: {e}")
            raise
    
    def add_memory(self, content):
        """Add a memory item to the system."""
        try:
            # Create memory item
            memory = {
                "content": content,
                "timestamp": time.time(),
                "id": str(len(self.memories) + 1)
            }
            
            # Generate vector embedding
            vector = self.model.encode(content)
            
            # Store memory and vector
            self.memories.append(memory)
            self.vectors.append(vector)
            
            logger.info(f"Added memory: {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def search_memory(self, query, limit=3):
        """Search for memories similar to the query."""
        try:
            if not self.memories:
                logger.warning("No memories to search")
                return []
            
            # Generate query vector
            query_vector = self.model.encode(query)
            
            # Calculate similarities
            similarities = cosine_similarity([query_vector], self.vectors)[0]
            
            # Get top matches
            top_indices = np.argsort(similarities)[-limit:][::-1]
            
            # Collect results
            results = []
            for idx in top_indices:
                memory = self.memories[idx].copy()
                memory["score"] = float(similarities[idx])
                results.append(memory)
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

def display_results(query, results):
    """Display search results in a formatted way."""
    print(f"\nQuery: \"{query}\"")
    
    if not results:
        print("No results found")
        return
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result['content']}")
        print(f"   Score: {result['score']:.4f}")
        print(f"   ID: {result['id']}")

def main():
    """Run the memory search test."""
    try:
        print("\n=== SEMANTIC MEMORY SEARCH TEST ===\n")
        
        # Initialize memory system
        memory = SimpleMemorySystem()
        
        # Add test memories
        print("Adding test memories...")
        test_memories = [
            "Python is a high-level programming language with dynamic typing and is great for data science.",
            "Machine learning models require large amounts of training data to achieve good performance.",
            "WebSockets provide real-time communication between client and server for fast data transfer.",
            "I need to remember to buy groceries this weekend, including milk, eggs, and bread.",
            "The memory system uses semantic search for retrieving relevant information based on meaning.",
            "Artificial intelligence is transforming how we interact with technology in everyday life.",
            "The weather forecast predicts rain tomorrow, so bring an umbrella if you go outside.",
            "Neural networks are inspired by the human brain and consist of layers of neurons."
        ]
        
        for memory_text in test_memories:
            memory.add_memory(memory_text)
        
        print(f"Added {len(test_memories)} memories to the system")
        
        # Test search queries
        print("\n=== TESTING SEMANTIC SEARCH ===\n")
        
        test_queries = [
            "Tell me about programming languages",
            "How does machine learning work?",
            "What is the best way to communicate between web clients and servers?",
            "What do I need to do this weekend?",
            "How does the memory search system work?",
            "Tell me about neural networks and AI",
            "What's the weather like tomorrow?",
            "Something completely unrelated to any stored memory"
        ]
        
        print("Running search tests with various queries...")
        
        for query in test_queries:
            results = memory.search_memory(query, limit=3)
            display_results(query, results)
        
        print("\n=== TEST COMPLETED ===\n")
        
    except Exception as e:
        logger.error(f"Error in memory search test: {e}")
        print(f"Error in memory search test: {e}")

if __name__ == "__main__":
    main()