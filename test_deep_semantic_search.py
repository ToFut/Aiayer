#!/usr/bin/env python3
"""
Deep Semantic Search Test Script
This script provides a comprehensive test of the semantic search capabilities
with detailed analysis and reporting.
"""

import sys
import os
import json
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

# Try to import the memory system
try:
    from memory.memory_system import MemorySystem
    from memory.semantic_search_agent import SemanticSearchAgent, search_memories, add_memory
except ImportError as e:
    print(f"Error importing memory modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepSemanticSearchTester:
    """
    Comprehensive tester for semantic search functionality with detailed metrics
    and analysis.
    """
    
    def __init__(self):
        """Initialize the tester."""
        self.memory_system = None
        self.search_agent = None
        self.test_results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'query_results': [],
            'memory_stats': {},
            'test_duration': 0
        }
        
    async def initialize(self):
        """Initialize memory system and search agent."""
        try:
            print("🧠 Initializing memory system...")
            self.memory_system = MemorySystem()
            print("✅ Memory system initialized")
            
            print("🔍 Initializing semantic search agent...")
            self.search_agent = SemanticSearchAgent()
            print("✅ Semantic search agent initialized")
            
            # Get memory stats
            self.test_results['memory_stats'] = {
                'short_term_count': len(self.memory_system.short_term_memory),
                'long_term_count': len(self.memory_system.long_term_memory),
                'vector_store_size': len(getattr(self.search_agent, 'vector_store', {}).documents)
                                    if hasattr(self.search_agent, 'vector_store') else 0
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def add_test_memories(self, count=5):
        """Add test memories if the system has too few memories."""
        try:
            # Check if we need to add test memories
            if self.test_results['memory_stats']['short_term_count'] + \
               self.test_results['memory_stats']['long_term_count'] < 5:
                
                print("📝 Adding test memories to system...")
                
                # Test data covering different domains
                test_memories = [
                    {
                        "content": "User is working on coding a Python application with Cursor editor",
                        "source": "test",
                        "tags": ["development", "python", "coding"]
                    },
                    {
                        "content": "Browser showing documentation for semantic search and vector embeddings",
                        "source": "test",
                        "tags": ["research", "ai", "documentation"]
                    },
                    {
                        "content": "User exploring memory system architecture and data flow",
                        "source": "test", 
                        "tags": ["architecture", "memory", "system"]
                    },
                    {
                        "content": "Terminal showing log output from memory system with error traces",
                        "source": "test",
                        "tags": ["debugging", "logs", "errors"]
                    },
                    {
                        "content": "User running test script to validate search functionality",
                        "source": "test",
                        "tags": ["testing", "validation", "search"]
                    }
                ]
                
                # Add memories
                for i, memory_data in enumerate(test_memories):
                    if i < count:
                        success = await add_memory(
                            content=memory_data["content"],
                            source=memory_data["source"],
                            tags=set(memory_data["tags"]),
                            metadata={"test_id": f"test_{i}"}
                        )
                        if success:
                            print(f"  ✅ Added test memory: {memory_data['content'][:50]}...")
                        else:
                            print(f"  ❌ Failed to add test memory")
                
                # Update stats
                if hasattr(self.search_agent, 'vector_store'):
                    self.test_results['memory_stats']['vector_store_size'] = \
                        len(self.search_agent.vector_store.documents)
                
                return True
            else:
                print("✅ System already has sufficient memories for testing")
                return True
                
        except Exception as e:
            logger.error(f"Error adding test memories: {e}")
            return False
    
    async def run_comprehensive_tests(self):
        """Run comprehensive semantic search tests."""
        start_time = time.time()
        
        try:
            print("\n🧪 RUNNING COMPREHENSIVE SEMANTIC SEARCH TESTS")
            print("=" * 60)
            
            # Define test queries with expected semantic matches
            test_queries = [
                {
                    "query": "development and coding",
                    "expected_keywords": ["coding", "python", "development"],
                    "description": "Basic development query"
                },
                {
                    "query": "memory architecture and system design",
                    "expected_keywords": ["memory", "architecture", "system"],
                    "description": "System architecture query"
                },
                {
                    "query": "debugging errors in logs",
                    "expected_keywords": ["error", "debug", "log"],
                    "description": "Error debugging query"
                },
                {
                    "query": "testing search functionality",
                    "expected_keywords": ["test", "search", "valid"],
                    "description": "Test validation query"
                },
                {
                    "query": "AI semantic vector embeddings",
                    "expected_keywords": ["semantic", "vector", "ai"],
                    "description": "Technical AI query"
                }
            ]
            
            for test_case in test_queries:
                self.test_results['total_tests'] += 1
                
                print(f"\n🔍 TEST QUERY: '{test_case['query']}'")
                print(f"  Description: {test_case['description']}")
                print(f"  Expected keywords: {', '.join(test_case['expected_keywords'])}")
                
                # Perform search
                try:
                    search_start = time.time()
                    results = await search_memories(test_case['query'], top_k=5)
                    search_time = time.time() - search_start
                    
                    print(f"  ⏱️  Search time: {search_time:.4f} seconds")
                    print(f"  📊 Found {len(results)} results")
                    
                    # Analyze results
                    if results:
                        keyword_matches = 0
                        total_score = 0
                        result_details = []
                        
                        for i, result in enumerate(results):
                            # Extract content
                            content = result.get('content', '')
                            score = result.get('similarity_score', 0)
                            total_score += score
                            
                            # Count keyword matches
                            matched_keywords = [kw for kw in test_case['expected_keywords'] 
                                               if kw.lower() in content.lower()]
                            keyword_matches += len(matched_keywords)
                            
                            print(f"    {i+1}. [{score:.3f}] {content[:50]}...")
                            if matched_keywords:
                                print(f"       Matched keywords: {', '.join(matched_keywords)}")
                            
                            # Store result details
                            result_details.append({
                                'content': content[:100] + "..." if len(content) > 100 else content,
                                'score': score,
                                'matched_keywords': matched_keywords
                            })
                        
                        # Calculate metrics
                        avg_score = total_score / len(results) if results else 0
                        keyword_coverage = len([kw for kw in test_case['expected_keywords'] 
                                              if any(kw.lower() in r.get('content', '').lower() for r in results)])
                        
                        test_result = {
                            'query': test_case['query'],
                            'description': test_case['description'],
                            'expected_keywords': test_case['expected_keywords'],
                            'result_count': len(results),
                            'search_time_seconds': search_time,
                            'average_score': avg_score,
                            'keyword_matches': keyword_matches,
                            'keyword_coverage': keyword_coverage,
                            'results': result_details,
                            'success': True if results and keyword_matches > 0 else False
                        }
                        
                        if test_result['success']:
                            self.test_results['successful_tests'] += 1
                            print(f"  ✅ Test PASSED: Found {keyword_matches} keyword matches")
                        else:
                            self.test_results['failed_tests'] += 1
                            print(f"  ❌ Test FAILED: No relevant results found")
                        
                        self.test_results['query_results'].append(test_result)
                        
                    else:
                        print("  ❌ No results found")
                        self.test_results['failed_tests'] += 1
                        self.test_results['query_results'].append({
                            'query': test_case['query'],
                            'description': test_case['description'],
                            'expected_keywords': test_case['expected_keywords'],
                            'result_count': 0,
                            'search_time_seconds': search_time,
                            'success': False
                        })
                        
                except Exception as e:
                    logger.error(f"Error in search test: {e}")
                    self.test_results['failed_tests'] += 1
                    self.test_results['query_results'].append({
                        'query': test_case['query'],
                        'description': test_case['description'],
                        'error': str(e),
                        'success': False
                    })
            
            # Test context-aware search
            try:
                print("\n🧠 TESTING CONTEXT-AWARE SEARCH")
                self.test_results['total_tests'] += 1
                
                # Perform context-aware search
                context_query = "Python development"
                app_context = "Cursor code editor"
                
                context_results = await search_memories(
                    context_query, 
                    top_k=3,
                    application_context=app_context  # Pass application context
                )
                
                if context_results:
                    print(f"  ✅ Context-aware search returned {len(context_results)} results")
                    self.test_results['successful_tests'] += 1
                    
                    # Store results
                    self.test_results['query_results'].append({
                        'query': context_query,
                        'description': "Context-aware search with application context",
                        'application_context': app_context,
                        'result_count': len(context_results),
                        'success': True
                    })
                else:
                    print("  ❌ Context-aware search failed")
                    self.test_results['failed_tests'] += 1
                    
                    self.test_results['query_results'].append({
                        'query': context_query,
                        'description': "Context-aware search with application context",
                        'application_context': app_context,
                        'result_count': 0,
                        'success': False
                    })
                
            except Exception as e:
                logger.error(f"Error in context-aware search test: {e}")
                self.test_results['failed_tests'] += 1
                
            # Calculate overall test duration
            self.test_results['test_duration'] = time.time() - start_time
            
            # Generate summary
            self.generate_test_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in comprehensive tests: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_test_summary(self):
        """Generate and print test summary."""
        try:
            print("\n📊 SEMANTIC SEARCH TEST SUMMARY")
            print("=" * 60)
            
            # Basic stats
            print(f"Total tests executed: {self.test_results['total_tests']}")
            print(f"Successful tests:    {self.test_results['successful_tests']}")
            print(f"Failed tests:        {self.test_results['failed_tests']}")
            success_rate = (self.test_results['successful_tests'] / 
                           self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0
            print(f"Success rate:        {success_rate:.1f}%")
            print(f"Test duration:       {self.test_results['test_duration']:.2f} seconds")
            
            # Memory stats
            print("\nMemory System Stats:")
            print(f"  Short-term memories: {self.test_results['memory_stats']['short_term_count']}")
            print(f"  Long-term memories:  {self.test_results['memory_stats']['long_term_count']}")
            print(f"  Vector store items:  {self.test_results['memory_stats']['vector_store_size']}")
            
            # Performance metrics
            if self.test_results['query_results']:
                avg_search_time = sum(r.get('search_time_seconds', 0) for r in self.test_results['query_results'] 
                                    if 'search_time_seconds' in r) / len(self.test_results['query_results'])
                print(f"\nPerformance Metrics:")
                print(f"  Average search time: {avg_search_time:.4f} seconds")
                
                # Calculate average score
                scores = [r.get('average_score', 0) for r in self.test_results['query_results'] 
                         if 'average_score' in r]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    print(f"  Average result score: {avg_score:.3f}")
                
                # Calculate keyword coverage
                coverages = [r.get('keyword_coverage', 0) / len(r.get('expected_keywords', []))
                           for r in self.test_results['query_results'] 
                           if 'keyword_coverage' in r and r.get('expected_keywords')]
                if coverages:
                    avg_coverage = sum(coverages) / len(coverages)
                    print(f"  Average keyword coverage: {avg_coverage:.1%}")
            
            # Overall assessment
            if success_rate >= 80:
                print("\n✅ OVERALL ASSESSMENT: Semantic search is working very well")
            elif success_rate >= 50:
                print("\n⚠️  OVERALL ASSESSMENT: Semantic search is working but needs improvement")
            else:
                print("\n❌ OVERALL ASSESSMENT: Semantic search is not working properly")
            
            # Save results to file
            results_file = "semantic_search_test_results.json"
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            print(f"\nDetailed test results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error generating test summary: {e}")

async def main():
    """Main entry point for the script."""
    print("🔍 DEEP SEMANTIC SEARCH TEST")
    print("=" * 60)
    
    tester = DeepSemanticSearchTester()
    
    # Initialize systems
    if not await tester.initialize():
        print("❌ Failed to initialize test systems")
        return
    
    # Add test memories if needed
    if not await tester.add_test_memories():
        print("⚠️ Warning: Failed to add test memories")
    
    # Run tests
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())