"""
Test PC questions with additional specific PC data added to memory.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the semantic search agent
from memory.semantic_search_agent import SemanticSearchAgent

# PC-specific data to add to memory
PC_DATA = [
    {
        "content": "User's macOS operating system version: Darwin 23.1.0",
        "source": "system_info",
        "metadata": {
            "type": "system_info",
            "os_type": "macOS",
            "os_version": "Darwin 23.1.0"
        }
    },
    {
        "content": "User has Chrome, Safari, VSCode, Terminal, Spotify, and Slack installed",
        "source": "app_inventory",
        "metadata": {
            "type": "application_list",
            "applications": ["Chrome", "Safari", "VSCode", "Terminal", "Spotify", "Slack"]
        }
    },
    {
        "content": "User opened Chrome and browsed to GitHub, Stack Overflow, and Gmail",
        "source": "browser_history",
        "metadata": {
            "application_name": "Google Chrome",
            "websites": ["github.com", "stackoverflow.com", "gmail.com"]
        }
    },
    {
        "content": "User edited semantic_search_agent.py file in VSCode project",
        "source": "file_activity",
        "metadata": {
            "application_name": "Visual Studio Code",
            "file_path": "/Users/user/project/memory/semantic_search_agent.py",
            "file_type": "python"
        }
    },
    {
        "content": "User installed Python packages: scikit-learn, numpy, matplotlib, and tensorflow",
        "source": "command_history",
        "metadata": {
            "application_name": "Terminal",
            "command": "pip install scikit-learn numpy matplotlib tensorflow",
            "packages": ["scikit-learn", "numpy", "matplotlib", "tensorflow"]
        }
    },
    {
        "content": "User uses Python for semantic search implementation and JavaScript for web interface",
        "source": "programming_activity",
        "metadata": {
            "languages": ["Python", "JavaScript"],
            "projects": ["semantic search", "web interface"]
        }
    },
    {
        "content": "User listening to 'Focus Flow' playlist on Spotify application",
        "source": "media_activity",
        "metadata": {
            "application_name": "Spotify",
            "content_type": "music",
            "playlist": "Focus Flow"
        }
    }
]

# PC questions to test
PC_QUESTIONS = [
    "What operating system is running on this computer?",
    "What applications are installed on this PC?",
    "What browser is the user using?",
    "What development environment does the user prefer?",
    "What was the last file the user edited?",
    "Has the user been using any media applications?",
    "What programming languages does the user work with?",
    "What websites does the user frequently visit?",
    "What packages or libraries has the user installed?",
    "What projects is the user working on currently?"
]

async def add_pc_data(agent):
    """Add PC-specific data to memory"""
    logger.info("📝 Adding PC-specific data to memory...")
    
    for data in PC_DATA:
        success = await agent.add_memory(
            content=data["content"],
            source=data["source"],
            metadata=data["metadata"]
        )
        
        if success:
            logger.info(f"  ✅ Added: {data['content']}")
        else:
            logger.error(f"  ❌ Failed to add: {data['content']}")
    
    # Wait for indexing
    logger.info("⏳ Waiting for indexing to complete...")
    time.sleep(2)

async def test_pc_questions(agent):
    """Test PC questions using semantic search"""
    logger.info("\n🔍 TESTING PC QUESTIONS")
    logger.info("=" * 70)
    
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
            min_similarity=0.15
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
                
                # Show relevance factors
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
        logger.info("✅ EXCELLENT: With proper data, the semantic search provides highly meaningful and accurate answers")
    elif quality_rate >= 60:
        logger.info("✅ GOOD: The semantic search provides useful answers to most PC questions")
    elif quality_rate >= 40:
        logger.info("⚠️ FAIR: The semantic search provides some useful information but has limitations")
    else:
        logger.info("❌ POOR: The semantic search has limited effectiveness even with added data")
    
    logger.info(f"Overall quality rate: {quality_rate:.1f}%")
    
    if success_rate > quality_rate:
        logger.info("Note: The search finds relevant information but quality could be improved.")
    elif quality_rate > 0 and found_results < len(PC_QUESTIONS):
        logger.info("Note: Some questions have no results, but when results are found, they are of good quality.")

async def main():
    """Run the main program"""
    logger.info("🧠 TESTING PC QUESTIONS WITH ADDED DATA")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    
    # Add PC data to memory
    await add_pc_data(search_agent)
    
    # Test PC questions
    await test_pc_questions(search_agent)

if __name__ == "__main__":
    asyncio.run(main())