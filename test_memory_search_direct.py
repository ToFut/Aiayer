#!/usr/bin/env python3
"""
Direct test of memory system and semantic search with specific PC-related queries
"""

import asyncio
import logging
import sys
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the semantic search agent
from memory.semantic_search_agent import SemanticSearchAgent

# PC questions to test
PC_QUESTIONS = [
    "What operating system is running on this computer?",
    "What applications are installed on my PC?",
    "What applications are currently running?",
    "What browser am I using?",
    "What development environment am I using?",
    "What was I working on recently?",
    "Am I listening to any music?",
    "What programming languages do I use?",
    "What's my current productivity level?",
    "How many applications do I have open?"
]

async def test_pc_questions():
    """Test PC questions using semantic search"""
    logger.info("\n🔍 TESTING MEMORY SYSTEM WITH PC QUESTIONS")
    logger.info("=" * 70)
    
    # Initialize agent
    agent = SemanticSearchAgent()
    
    # Track statistics
    found_results = 0
    high_quality = 0
    medium_quality = 0
    total_results = 0
    
    for question in PC_QUESTIONS:
        logger.info(f"\nQuestion: \"{question}\"")
        
        # Search memory
        start_time = time.time()
        results = await agent.search_memories(
            query=question,
            top_k=3,
            min_similarity=0.1  # Lower threshold to get more results
        )
        search_time = time.time() - start_time
        
        # Track statistics
        total_results += len(results) if results else 0
        found_results += 1 if results else 0
        
        if results:
            # Determine the best result and its quality
            best_score = max([r.similarity_score for r in results])
            if best_score > 0.4:
                quality = "High"
                high_quality += 1
            elif best_score > 0.2:
                quality = "Medium"
                medium_quality += 1
            else:
                quality = "Low"
            
            # Show results
            logger.info(f"Found {len(results)} results in {search_time:.4f}s - Quality: {quality}")
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. [{result.similarity_score:.3f}] {result.content}")
                
                # Show relevance factors if available
                if hasattr(result, "relevance_factors") and result.relevance_factors:
                    logger.info(f"   Relevance: {', '.join(result.relevance_factors)}")
        else:
            logger.info(f"No results found in {search_time:.4f}s")
    
    # Show summary statistics
    logger.info("\n📊 SUMMARY STATISTICS")
    logger.info("=" * 70)
    success_rate = found_results / len(PC_QUESTIONS) * 100
    quality_rate = (high_quality + medium_quality) / len(PC_QUESTIONS) * 100
    avg_results = total_results / len(PC_QUESTIONS)
    
    logger.info(f"Questions with results: {found_results}/{len(PC_QUESTIONS)} ({success_rate:.1f}%)")
    logger.info(f"High quality answers: {high_quality}/{len(PC_QUESTIONS)} ({high_quality/len(PC_QUESTIONS)*100:.1f}%)")
    logger.info(f"Medium quality answers: {medium_quality}/{len(PC_QUESTIONS)} ({medium_quality/len(PC_QUESTIONS)*100:.1f}%)")
    logger.info(f"Average results per question: {avg_results:.1f}")
    
    # Final assessment
    logger.info("\n🎯 FINAL ASSESSMENT")
    logger.info("=" * 70)
    if quality_rate >= 80:
        logger.info("✅ EXCELLENT: Memory system provides highly meaningful and accurate answers")
    elif quality_rate >= 60:
        logger.info("✅ GOOD: Memory system provides useful answers to most PC questions")
    elif quality_rate >= 40:
        logger.info("⚠️ FAIR: Memory system provides some useful information but has limitations")
    else:
        logger.info("❌ POOR: Memory system has limited effectiveness for PC-related queries")
    
    logger.info(f"Overall quality rate: {quality_rate:.1f}%")

if __name__ == "__main__":
    logger.info("🧠 TESTING DIRECT MEMORY SEARCH")
    logger.info("=" * 70)
    
    asyncio.run(test_pc_questions())