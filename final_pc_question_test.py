"""
Final test of PC questions using semantic search with direct queries
for specific questions.
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

# Targeted PC data with clearer content
TARGETED_PC_DATA = [
    {
        "content": "System Information: macOS (Darwin 23.1.0) running on user's computer",
        "source": "system_info",
        "metadata": {"type": "os_info"}
    },
    {
        "content": "Installed Applications: Google Chrome, Visual Studio Code, Terminal, Spotify, Slack",
        "source": "app_inventory",
        "metadata": {"type": "application_list"}
    },
    {
        "content": "Default Browser: User primarily uses Google Chrome for web browsing",
        "source": "user_preferences",
        "metadata": {"type": "browser_preference"}
    },
    {
        "content": "Development Environment: Visual Studio Code is the main IDE for coding projects",
        "source": "user_preferences",
        "metadata": {"type": "dev_environment"}
    },
    {
        "content": "Recently Edited File: semantic_search_agent.py in the memory directory",
        "source": "file_activity",
        "metadata": {"type": "file_edit", "file_name": "semantic_search_agent.py"}
    },
    {
        "content": "Media Application Usage: User regularly listens to Spotify while working",
        "source": "app_usage",
        "metadata": {"type": "media_usage"}
    },
    {
        "content": "Programming Languages: Python (primary) and JavaScript (secondary) for development",
        "source": "coding_activity",
        "metadata": {"type": "languages"}
    },
    {
        "content": "Frequently Visited Websites: GitHub, Stack Overflow, Gmail, and Google Search",
        "source": "browser_history",
        "metadata": {"type": "web_usage"}
    },
    {
        "content": "Installed Libraries: scikit-learn, numpy, matplotlib, tensorflow for Python projects",
        "source": "package_info",
        "metadata": {"type": "libraries"}
    },
    {
        "content": "Current Projects: Semantic search implementation and UI automation framework",
        "source": "user_activity",
        "metadata": {"type": "projects"}
    }
]

# Direct questions with expected keywords in the answers
DIRECT_QUESTIONS = [
    {
        "question": "What operating system is running on this computer?",
        "expected": ["macOS", "Darwin"]
    },
    {
        "question": "What applications are installed on this PC?",
        "expected": ["Chrome", "VSCode", "Spotify", "Slack"]
    },
    {
        "question": "What browser is the user using?",
        "expected": ["Chrome", "Google Chrome"]
    },
    {
        "question": "What development environment does the user prefer?",
        "expected": ["VSCode", "Visual Studio Code"]
    },
    {
        "question": "What was the last file the user edited?",
        "expected": ["semantic_search_agent.py"]
    },
    {
        "question": "Has the user been using any media applications?",
        "expected": ["Spotify"]
    },
    {
        "question": "What programming languages does the user work with?",
        "expected": ["Python", "JavaScript"]
    },
    {
        "question": "What websites does the user frequently visit?",
        "expected": ["GitHub", "Stack Overflow", "Gmail"]
    },
    {
        "question": "What packages or libraries has the user installed?",
        "expected": ["scikit-learn", "numpy", "matplotlib", "tensorflow"]
    },
    {
        "question": "What projects is the user working on currently?",
        "expected": ["semantic search", "UI automation"]
    }
]

async def add_targeted_data(agent):
    """Add targeted PC data to memory"""
    logger.info("📝 Adding targeted PC data...")
    
    for data in TARGETED_PC_DATA:
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

async def test_direct_questions(agent):
    """Test direct questions about PC information"""
    logger.info("\n🔍 TESTING DIRECT PC QUESTIONS")
    logger.info("=" * 70)
    
    results = []
    
    for item in DIRECT_QUESTIONS:
        question = item["question"]
        expected = item["expected"]
        
        logger.info(f"\nQuestion: \"{question}\"")
        logger.info(f"Expected keywords: {', '.join(expected)}")
        
        # Search with the question
        start_time = time.time()
        search_results = await agent.search_memories(
            query=question,
            top_k=3,
            min_similarity=0.15
        )
        search_time = time.time() - start_time
        
        if search_results:
            # Log results
            logger.info(f"Found {len(search_results)} results in {search_time:.4f}s")
            
            # Check for expected keywords
            found_keywords = []
            for keyword in expected:
                for result in search_results:
                    if keyword.lower() in result.content.lower():
                        found_keywords.append(keyword)
                        break
            
            # Calculate score
            success_percent = len(found_keywords) / len(expected) * 100 if expected else 0
            
            # Determine quality
            top_similarity = search_results[0].similarity_score
            if top_similarity > 0.6:
                quality = "Excellent"
            elif top_similarity > 0.4:
                quality = "Good"
            elif top_similarity > 0.2:
                quality = "Fair"
            else:
                quality = "Poor"
                
            # Show results details
            for i, result in enumerate(search_results, 1):
                logger.info(f"{i}. [{result.similarity_score:.3f}] {result.content}")
                
                # Show relevance factors if available
                if hasattr(result, "relevance_factors") and result.relevance_factors:
                    logger.info(f"   Relevance: {', '.join(result.relevance_factors)}")
            
            # Summarize findings
            if found_keywords:
                logger.info(f"✅ Found {len(found_keywords)}/{len(expected)} expected keywords ({success_percent:.1f}%)")
                logger.info(f"   Found: {', '.join(found_keywords)}")
                if len(found_keywords) < len(expected):
                    missing = [k for k in expected if k not in found_keywords]
                    logger.info(f"   Missing: {', '.join(missing)}")
            else:
                logger.info(f"❌ Did not find any expected keywords")
            
            logger.info(f"Quality: {quality} (similarity: {top_similarity:.3f})")
            
            # Store result
            results.append({
                "question": question,
                "found_percent": success_percent,
                "quality": quality,
                "top_similarity": top_similarity
            })
        else:
            logger.info(f"No results found ({search_time:.4f}s)")
            logger.info("❌ Search failed to find any relevant information")
            
            results.append({
                "question": question,
                "found_percent": 0,
                "quality": "Failed",
                "top_similarity": 0
            })
    
    # Calculate overall statistics
    success_rate = sum(1 for r in results if r["found_percent"] > 0) / len(results) * 100
    keyword_rate = sum(r["found_percent"] for r in results) / len(results)
    avg_similarity = sum(r["top_similarity"] for r in results) / len(results)
    
    quality_counts = {}
    for r in results:
        q = r["quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1
    
    # Show summary
    logger.info("\n📊 SUMMARY STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Questions tested: {len(results)}")
    logger.info(f"Questions with results: {sum(1 for r in results if r['found_percent'] > 0)}/{len(results)} ({success_rate:.1f}%)")
    logger.info(f"Average keyword match rate: {keyword_rate:.1f}%")
    logger.info(f"Average top similarity score: {avg_similarity:.3f}")
    
    # Show quality distribution
    logger.info("\nQuality distribution:")
    for quality, count in quality_counts.items():
        percent = count / len(results) * 100
        logger.info(f"- {quality}: {count}/{len(results)} ({percent:.1f}%)")
    
    # Final assessment
    high_quality = quality_counts.get("Excellent", 0) + quality_counts.get("Good", 0)
    high_quality_rate = high_quality / len(results) * 100
    
    logger.info("\n🎯 FINAL ASSESSMENT")
    logger.info("=" * 70)
    if high_quality_rate >= 70:
        logger.info("✅ EXCELLENT: Semantic search provides highly accurate and relevant results for PC questions")
    elif high_quality_rate >= 50:
        logger.info("✅ GOOD: Semantic search provides useful answers for most PC questions")
    elif high_quality_rate >= 30:
        logger.info("⚠️ FAIR: Semantic search provides some useful information but has limitations")
    else:
        logger.info("❌ POOR: Semantic search struggles to provide high-quality answers for PC questions")
    
    logger.info(f"High-quality answer rate: {high_quality_rate:.1f}%")

async def main():
    """Run the final PC question test"""
    logger.info("🔍 FINAL PC QUESTION TEST")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    
    # Add targeted data
    await add_targeted_data(search_agent)
    
    # Test direct questions
    await test_direct_questions(search_agent)
    
    logger.info("\n✅ TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())