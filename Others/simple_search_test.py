#!/usr/bin/env python3
"""
Simple Memory Search Test

This script tests basic search functionality without requiring external models.
"""
import os
import json
import time
import logging
import re
from collections import Counter
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_search_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleSearch:
    """A very simple search system using basic text matching."""
    
    def __init__(self):
        """Initialize the search system."""
        self.memories = []
        logger.info("SimpleSearch initialized")
        print("Search system initialized")
    
    def add_memory(self, content):
        """Add a memory item to the system."""
        try:
            # Create memory item
            memory = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "id": str(len(self.memories) + 1),
                "tokens": self._tokenize(content)
            }
            
            # Store memory
            self.memories.append(memory)
            
            logger.info(f"Added memory: {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def _tokenize(self, text):
        """Convert text to lowercase tokens."""
        # Convert to lowercase and split by non-alphanumeric characters
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
    """Run the search test."""
    try:
        print("\n=== SIMPLE MEMORY SEARCH TEST ===\n")
        
        # Initialize search system
        search = SimpleSearch()
        
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
            search.add_memory(memory_text)
        
        print(f"Added {len(test_memories)} memories to the system")
        
        # Test search queries
        print("\n=== TESTING SEARCH ===\n")
        
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
            results = search.search(query, limit=3)
            display_results(query, results)
        
        print("\n=== TEST COMPLETED ===\n")
        
    except Exception as e:
        logger.error(f"Error in search test: {e}")
        print(f"Error in search test: {e}")

if __name__ == "__main__":
    main()