"""
Add realistic user activity data to memory and demonstrate searching through it.
This simulates the kind of content that would be collected during normal system usage.
"""

import asyncio
import logging
import time
import json
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

# Realistic user activity data
REALISTIC_USER_ACTIVITIES = [
    {
        "content": "User opened Chrome browser and navigated to gmail.com to check emails",
        "source": "process_sensor",
        "metadata": {
            "application_name": "Google Chrome",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "activity_type": "browser_navigation",
            "url": "https://gmail.com"
        }
    },
    {
        "content": "User searched for 'python async websocket example' on Google",
        "source": "screen_sensor",
        "metadata": {
            "application_name": "Google Chrome",
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
            "activity_type": "search_query",
            "search_engine": "Google"
        }
    },
    {
        "content": "User opened VSCode and worked on semantic_search_agent.py file",
        "source": "file_sensor",
        "metadata": {
            "application_name": "Visual Studio Code",
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=30)).isoformat(),
            "activity_type": "file_edit",
            "file_path": "/Users/user/project/memory/semantic_search_agent.py"
        }
    },
    {
        "content": "User visited Stack Overflow to read about 'python vector embeddings for semantic search'",
        "source": "screen_sensor",
        "metadata": {
            "application_name": "Google Chrome",
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=15)).isoformat(),
            "activity_type": "website_visit",
            "url": "https://stackoverflow.com/questions/tagged/vector-embeddings+python"
        }
    },
    {
        "content": "User opened Terminal and ran 'pip install scikit-learn numpy' command",
        "source": "process_sensor",
        "metadata": {
            "application_name": "Terminal",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "activity_type": "command_execution",
            "command": "pip install scikit-learn numpy"
        }
    },
    {
        "content": "User testing embedding function with TF-IDF in Python console",
        "source": "screen_sensor",
        "metadata": {
            "application_name": "Visual Studio Code",
            "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
            "activity_type": "coding",
            "code_context": "vector embeddings, TF-IDF"
        }
    },
    {
        "content": "User opened Spotify and played 'Focus Flow' playlist while coding",
        "source": "process_sensor",
        "metadata": {
            "application_name": "Spotify",
            "timestamp": (datetime.now() - timedelta(minutes=40)).isoformat(),
            "activity_type": "media_playback",
            "content": "Focus Flow playlist"
        }
    },
    {
        "content": "User checked GitHub repository issues related to semantic search implementation",
        "source": "screen_sensor",
        "metadata": {
            "application_name": "Google Chrome",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "activity_type": "website_visit",
            "url": "https://github.com/user/project/issues"
        }
    },
    {
        "content": "User switched to Slack to message team about semantic search progress",
        "source": "process_sensor",
        "metadata": {
            "application_name": "Slack",
            "timestamp": (datetime.now() - timedelta(minutes=20)).isoformat(),
            "activity_type": "communication",
            "channel": "team-ai-projects"
        }
    },
    {
        "content": "User looking at visualization of vector embeddings using matplotlib",
        "source": "screen_sensor",
        "metadata": {
            "application_name": "Visual Studio Code",
            "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "activity_type": "data_visualization",
            "library": "matplotlib"
        }
    }
]

# Questions to ask about user activities
USER_QUESTIONS = [
    "What websites has the user visited recently?",
    "Has the user been working on any coding projects?",
    "What applications has the user used today?",
    "Did the user search for anything online?",
    "Is the user working on something related to semantic search?",
    "What music has the user been listening to?",
    "Has the user communicated with anyone?",
    "What development tools has the user been using?",
    "What was the user doing in the last hour?",
    "What files has the user been working on?"
]

async def add_realistic_activities(search_agent):
    """Add realistic user activities to memory"""
    logger.info("📝 Adding realistic user activities to memory...")
    
    for activity in REALISTIC_USER_ACTIVITIES:
        # Format the metadata timestamp for display
        display_time = "unknown"
        if "timestamp" in activity["metadata"]:
            try:
                ts = activity["metadata"]["timestamp"]
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                    display_time = dt.strftime("%H:%M:%S")
            except:
                pass
                
        success = await search_agent.add_memory(
            content=activity["content"],
            source=activity["source"],
            metadata=activity["metadata"]
        )
        
        if success:
            logger.info(f"  ✅ [{display_time}] {activity['content']}")
        else:
            logger.error(f"  ❌ Failed to add: {activity['content']}")
    
    # Wait for indexing
    logger.info("⏳ Allowing time for indexing...")
    time.sleep(2)

async def answer_user_questions(search_agent):
    """Answer questions about user activities using semantic search"""
    logger.info("\n🔍 ANSWERING QUESTIONS ABOUT USER ACTIVITIES")
    logger.info("=" * 70)
    
    for i, question in enumerate(USER_QUESTIONS, 1):
        logger.info(f"\n{i}. Question: \"{question}\"")
        
        # Search for relevant activities
        start_time = time.time()
        results = await search_agent.search_memories(
            query=question,
            top_k=3,
            min_similarity=0.15
        )
        search_time = time.time() - start_time
        
        if results:
            logger.info(f"   Found {len(results)} relevant activities in {search_time:.4f}s:")
            
            # Generate answer based on search results
            answer = generate_answer(question, results)
            
            # Show results and answer
            for j, result in enumerate(results, 1):
                # Format the timestamp for display
                display_time = "unknown time"
                if hasattr(result, "metadata") and result.metadata and "timestamp" in result.metadata:
                    try:
                        ts = result.metadata["timestamp"]
                        if isinstance(ts, str):
                            dt = datetime.fromisoformat(ts)
                            display_time = dt.strftime("%H:%M:%S")
                    except:
                        pass
                
                # Get app name
                app_name = None
                if hasattr(result, "metadata") and result.metadata:
                    app_name = result.metadata.get("application_name")
                
                # Display the result
                logger.info(f"   {j}. [{result.similarity_score:.3f}] {result.content}")
                if app_name:
                    logger.info(f"      App: {app_name} | Time: {display_time}")
            
            # Show the generated answer
            logger.info(f"\n   💬 Answer: {answer}")
        else:
            logger.info(f"   No relevant activities found ({search_time:.4f}s)")
            logger.info(f"\n   💬 Answer: I don't have information about that in my memory.")

def generate_answer(question, results):
    """Generate a natural language answer based on search results"""
    if not results:
        return "I don't have information about that in my memory."
    
    # Extract relevant information
    activities = [r.content for r in results]
    apps = []
    times = []
    
    for r in results:
        if hasattr(r, "metadata") and r.metadata:
            if "application_name" in r.metadata:
                apps.append(r.metadata["application_name"])
            if "timestamp" in r.metadata:
                try:
                    ts = r.metadata["timestamp"]
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts)
                        times.append(dt)
                except:
                    pass
    
    # Generate different answers based on question type
    if "websites" in question.lower() or "visited" in question.lower():
        websites = [a for a in activities if "visited" in a or "navigated" in a or "Chrome" in a]
        if websites:
            return f"The user has visited several websites recently, including: {', '.join([w.split('visited')[1].strip() if 'visited' in w else w for w in websites[:2]])}."
        
    elif "coding" in question.lower() or "projects" in question.lower():
        coding = [a for a in activities if "VSCode" in a or "coding" in a or "code" in a]
        if coding:
            return f"Yes, the user has been working on coding projects. They were {coding[0].lower().replace('User ', '')}."
            
    elif "applications" in question.lower() or "apps" in question.lower():
        if apps:
            unique_apps = list(set(apps))
            return f"The user has used several applications today, including {', '.join(unique_apps)}."
            
    elif "search" in question.lower():
        searches = [a for a in activities if "searched" in a]
        if searches:
            return f"Yes, the user {searches[0].lower().replace('User ', '')}."
            
    elif "semantic search" in question.lower():
        semantic = [a for a in activities if "semantic" in a or "embedding" in a or "vector" in a]
        if semantic:
            return f"Yes, the user has been working on semantic search related tasks. They were {semantic[0].lower().replace('User ', '')}."
            
    elif "music" in question.lower() or "listening" in question.lower():
        music = [a for a in activities if "Spotify" in a or "played" in a or "music" in a]
        if music:
            return f"The user {music[0].lower().replace('User ', '')}."
            
    elif "communicated" in question.lower() or "message" in question.lower():
        comms = [a for a in activities if "Slack" in a or "message" in a or "email" in a]
        if comms:
            return f"Yes, the user {comms[0].lower().replace('User ', '')}."
            
    elif "development tools" in question.lower():
        tools = [a for a in activities if "VSCode" in a or "Terminal" in a or "GitHub" in a]
        if tools:
            tool_names = []
            for t in tools:
                if "VSCode" in t:
                    tool_names.append("Visual Studio Code")
                if "Terminal" in t:
                    tool_names.append("Terminal")
                if "GitHub" in t:
                    tool_names.append("GitHub")
            return f"The user has been using various development tools including {', '.join(set(tool_names))}."
            
    elif "last hour" in question.lower():
        recent = []
        now = datetime.now()
        for r in results:
            if hasattr(r, "metadata") and r.metadata and "timestamp" in r.metadata:
                try:
                    ts = r.metadata["timestamp"]
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts)
                        if (now - dt).total_seconds() < 3600:
                            recent.append(r.content)
                except:
                    pass
        
        if recent:
            return f"In the last hour, the user has {recent[0].lower().replace('User ', '')}."
            
    elif "files" in question.lower():
        files = [a for a in activities if ".py" in a or "file" in a]
        if files:
            return f"The user has been working with files, particularly {files[0].lower().replace('User ', '')}."
    
    # Default answer based on top result
    return f"Based on my memory, the user {results[0].content.lower().replace('User ', '')}."

async def main():
    """Run the main program"""
    logger.info("🌟 REALISTIC USER ACTIVITY MEMORY SEARCH")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    
    # Add realistic user activities
    await add_realistic_activities(search_agent)
    
    # Answer questions about user activities
    await answer_user_questions(search_agent)
    
    # Show summary
    logger.info("\n✅ DEMONSTRATION COMPLETE")
    logger.info("=" * 70)
    logger.info("The semantic search system can now effectively:")
    logger.info("1. Store detailed information about user activities")
    logger.info("2. Recall activities based on natural language queries")
    logger.info("3. Provide contextually relevant answers about user behavior")
    logger.info("4. Search across different applications and activity types")
    logger.info("5. Find information based on semantic understanding, not just keywords")

if __name__ == "__main__":
    asyncio.run(main())