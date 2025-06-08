"""
Search through memory for information about user activities
and demonstrate how the system can recall what the user has been doing.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the semantic search agent
from memory.semantic_search_agent import SemanticSearchAgent

# Queries about user activities
USER_ACTIVITY_QUERIES = [
    "what applications has the user been using",
    "websites the user visited recently",
    "search queries the user has made",
    "user's recent interactions with Google",
    "coding or development activities",
    "what tasks was the user working on",
    "what content has the user viewed",
    "applications user opened recently",
    "user's most frequent activities",
    "what did the user search for online"
]

async def search_user_activities():
    """Search memory for information about user activities"""
    logger.info("🔍 SEARCHING USER ACTIVITIES IN MEMORY")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    
    # Get memory stats
    stats = search_agent.get_performance_metrics()
    logger.info(f"📊 Memory contains {stats.get('total_documents', 'N/A')} documents")
    
    # Run each query about user activities
    found_activities = []
    
    for query in USER_ACTIVITY_QUERIES:
        logger.info(f"\n🔎 Query: '{query}'")
        
        start_time = time.time()
        results = await search_agent.search_memories(
            query=query,
            top_k=3,
            min_similarity=0.15
        )
        search_time = time.time() - start_time
        
        logger.info(f"   Found {len(results)} results in {search_time:.4f}s")
        
        for i, result in enumerate(results, 1):
            # Skip if content is too similar to something we've already shown
            if any(existing_content in result.content or result.content in existing_content 
                  for existing_content in found_activities):
                continue
                
            # Extract key information
            content = result.content[:150] + "..." if len(result.content) > 150 else result.content
            similarity = result.similarity_score
            source = result.source if hasattr(result, "source") else "unknown"
            
            # Get timestamp
            timestamp = "unknown"
            if hasattr(result, "timestamp"):
                if isinstance(result.timestamp, datetime):
                    timestamp = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = str(result.timestamp)
            
            # Get application name from metadata if available
            app_name = None
            if hasattr(result, "metadata") and result.metadata:
                app_name = result.metadata.get("application_name", result.metadata.get("app_name"))
            
            # Log the result
            logger.info(f"   {i}. [{similarity:.3f}] {content}")
            if app_name:
                logger.info(f"      App: {app_name}")
            logger.info(f"      Source: {source} | Time: {timestamp}")
            
            # Add to found activities to avoid showing duplicates
            found_activities.append(result.content)
            
            # Stop after finding 10 unique activities
            if len(found_activities) >= 10:
                break
        
        # Stop after finding 10 unique activities
        if len(found_activities) >= 10:
            logger.info("\n✅ Found sufficient unique user activities")
            break
    
    # Summarize findings
    logger.info("\n📋 USER ACTIVITY SUMMARY")
    logger.info("=" * 70)
    
    if found_activities:
        logger.info(f"Found {len(found_activities)} unique user activities in memory:")
        for i, activity in enumerate(found_activities, 1):
            short_activity = activity[:150] + "..." if len(activity) > 150 else activity
            logger.info(f"{i}. {short_activity}")
    else:
        logger.info("No specific user activities found in memory.")
    
    logger.info("\n💡 The semantic search system can successfully recall user activities from memory.")
    logger.info("This enables contextual awareness about what the user has been doing.")

if __name__ == "__main__":
    asyncio.run(search_user_activities())