#!/usr/bin/env python3
"""
Test Memory Search Meaningfulness
Tests the improved memory system to verify meaningful search results
"""
import json
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add memory module to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')
from memory.memory_system import MemorySystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_memory_meaningfulness():
    """Test the memory system for meaningful content and search"""
    logger.info("🧪 Testing Memory System Meaningfulness...")
    
    try:
        # Initialize memory system
        memory_system = MemorySystem()
        
        # Test 1: Check current memory quality
        logger.info("\n📊 Test 1: Analyzing current memory quality")
        await analyze_memory_quality(memory_system)
        
        # Test 2: Test semantic search
        logger.info("\n🔍 Test 2: Testing semantic search functionality")
        await test_semantic_search(memory_system)
        
        # Test 3: Test context retrieval
        logger.info("\n🧠 Test 3: Testing context-aware retrieval")
        await test_context_retrieval(memory_system)
        
        # Test 4: Test professional context understanding
        logger.info("\n💼 Test 4: Testing professional context understanding")
        await test_professional_context(memory_system)
        
        logger.info("\n✅ Memory meaningfulness testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

async def analyze_memory_quality(memory_system):
    """Analyze the quality of stored memories"""
    try:
        # Get all memories
        memories = memory_system.short_term_memory + memory_system.long_term_memory
        
        if not memories:
            logger.warning("No memories found to analyze")
            return
        
        logger.info(f"Found {len(memories)} memories to analyze")
        
        # Quality metrics
        meaningful_count = 0
        has_insights_count = 0
        has_topics_count = 0
        high_productivity_count = 0
        professional_context_count = 0
        
        for memory in memories:
            # Check if memory has meaningful interaction
            if memory.get('context_analysis', {}).get('meaningful_interaction'):
                meaningful_count += 1
            
            # Check for insights
            if memory.get('insights', []):
                has_insights_count += 1
                logger.info(f"  💡 Memory insights: {memory['insights']}")
            
            # Check for semantic analysis
            if memory.get('content_analysis', {}).get('key_topics', []):
                has_topics_count += 1
                topics = memory['content_analysis']['key_topics']
                logger.info(f"  🏷️  Key topics: {topics}")
            
            # Check productivity categorization
            if memory.get('productivity_category') == 'highly_productive':
                high_productivity_count += 1
            
            # Check professional context
            prof_context = memory.get('professional_context', {})
            if prof_context.get('domain') and prof_context['domain'] != 'unknown':
                professional_context_count += 1
                logger.info(f"  💼 Professional context: {prof_context}")
        
        # Report quality metrics
        total = len(memories)
        logger.info(f"\n📈 Quality Metrics:")
        logger.info(f"  Meaningful interactions: {meaningful_count}/{total} ({meaningful_count/total*100:.1f}%)")
        logger.info(f"  Memories with insights: {has_insights_count}/{total} ({has_insights_count/total*100:.1f}%)")
        logger.info(f"  Memories with topics: {has_topics_count}/{total} ({has_topics_count/total*100:.1f}%)")
        logger.info(f"  High productivity memories: {high_productivity_count}/{total} ({high_productivity_count/total*100:.1f}%)")
        logger.info(f"  Professional context detected: {professional_context_count}/{total} ({professional_context_count/total*100:.1f}%)")
        
        # Overall quality score
        quality_score = (meaningful_count + has_insights_count + has_topics_count + professional_context_count) / (total * 4) * 100
        logger.info(f"  Overall Quality Score: {quality_score:.1f}%")
        
        if quality_score > 70:
            logger.info("  ✅ Memory quality is GOOD")
        elif quality_score > 40:
            logger.info("  ⚠️  Memory quality is MODERATE")
        else:
            logger.info("  ❌ Memory quality is POOR")
        
    except Exception as e:
        logger.error(f"Error analyzing memory quality: {e}")

async def test_semantic_search(memory_system):
    """Test semantic search functionality"""
    try:
        # Test queries
        test_queries = [
            "development work coding",
            "AI assisted programming",
            "productivity and workflow",
            "software engineering tasks",
            "cursor editor development"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔎 Searching for: '{query}'")
            
            results = await memory_system.search_memory(
                query=query,
                limit=3,
                context_aware=True
            )
            
            if results:
                logger.info(f"  Found {len(results)} relevant results:")
                for i, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    memory_type = result.get('memory_type', 'unknown')
                    content_preview = result.get('content', '')[:100] + "..."
                    logger.info(f"    {i}. Score: {score:.3f} | Type: {memory_type}")
                    logger.info(f"       Preview: {content_preview}")
            else:
                logger.warning(f"  No results found for '{query}'")
        
    except Exception as e:
        logger.error(f"Error testing semantic search: {e}")

async def test_context_retrieval(memory_system):
    """Test context-aware memory retrieval"""
    try:
        logger.info("Testing context-aware retrieval...")
        
        # Get recent memories
        memories = memory_system.short_term_memory
        if not memories:
            logger.warning("No short-term memories for context testing")
            return
        
        # Test context retrieval for the most recent memory
        recent_memory = memories[-1]
        memory_id = recent_memory.get('memory_id')
        
        if memory_id:
            logger.info(f"Getting context for memory: {memory_id}")
            
            related_memories = await memory_system.get_related_memories(
                memory_id=memory_id,
                limit=3
            )
            
            if related_memories:
                logger.info(f"  Found {len(related_memories)} related memories:")
                for memory in related_memories:
                    relevance = memory.get('relevance', 0)
                    relationship = memory.get('relationship_type', 'unknown')
                    logger.info(f"    Relevance: {relevance:.3f} | Relationship: {relationship}")
            else:
                logger.warning("  No related memories found")
        
    except Exception as e:
        logger.error(f"Error testing context retrieval: {e}")

async def test_professional_context(memory_system):
    """Test professional context understanding"""
    try:
        logger.info("Testing professional context understanding...")
        
        # Check for development-related memories
        dev_memories = []
        for memory in memory_system.short_term_memory:
            activity = memory.get('user_activity', {})
            if activity.get('primary_activity') == 'development':
                dev_memories.append(memory)
        
        if dev_memories:
            logger.info(f"Found {len(dev_memories)} development-related memories")
            
            for memory in dev_memories:
                app = memory.get('user_activity', {}).get('application_used', '')
                insights = memory.get('insights', [])
                workflow = memory.get('workflow_insights', '')
                
                logger.info(f"  App: {app}")
                logger.info(f"  Insights: {insights}")
                logger.info(f"  Workflow: {workflow}")
        else:
            logger.warning("No development-related memories found")
        
    except Exception as e:
        logger.error(f"Error testing professional context: {e}")

def main():
    """Main entry point"""
    print("🧪 Testing Memory System Meaningfulness")
    print("=" * 50)
    
    # Run async test
    asyncio.run(test_memory_meaningfulness())

if __name__ == "__main__":
    main()