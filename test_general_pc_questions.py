"""
Test asking general questions about the PC to see if the semantic search 
provides meaningful answers from memory.
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

# General PC questions to test
PC_QUESTIONS = [
    "What operating system is running on this computer?",
    "What applications are installed on this PC?",
    "What browser is the user using?",
    "What development environment does the user prefer?",
    "What was the last file the user edited?",
    "Has the user been using any media applications?",
    "What programming languages does the user work with?",
    "What websites does the user frequently visit?",
    "What's the most recent application the user opened?",
    "What projects is the user working on currently?"
]

async def search_memory_for_answer(agent, question):
    """Search memory for an answer to the question"""
    logger.info(f"\n🔍 Question: \"{question}\"")
    
    # Perform search
    start_time = time.time()
    results = await agent.search_memories(
        query=question,
        top_k=3,
        min_similarity=0.15
    )
    search_time = time.time() - start_time
    
    if results:
        logger.info(f"   Found {len(results)} relevant memories in {search_time:.4f}s")
        
        # Show top results
        for i, result in enumerate(results[:3], 1):
            # Get app name and time from metadata if available
            app_name = "Unknown"
            timestamp = "Unknown time"
            
            if hasattr(result, "metadata") and result.metadata:
                if "application_name" in result.metadata:
                    app_name = result.metadata["application_name"]
                if "timestamp" in result.metadata:
                    try:
                        ts = result.metadata["timestamp"]
                        if isinstance(ts, str):
                            dt = datetime.fromisoformat(ts)
                            timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
            
            # Display the result
            logger.info(f"   {i}. [{result.similarity_score:.3f}] {result.content}")
            logger.info(f"      App: {app_name} | Time: {timestamp}")
            
            # Show relevance factors if available
            if hasattr(result, "relevance_factors") and result.relevance_factors:
                logger.info(f"      Relevance: {', '.join(result.relevance_factors)}")
        
        # Generate answer based on top results
        answer = generate_answer(question, results)
        logger.info(f"\n   💡 Answer: {answer}")
        
        # Evaluate answer quality
        quality = evaluate_answer_quality(question, answer, results)
        logger.info(f"   Quality: {quality}")
        
        return answer, quality
    else:
        logger.info(f"   No relevant memories found ({search_time:.4f}s)")
        logger.info(f"\n   💡 Answer: I don't have enough information in memory to answer that question.")
        logger.info(f"   Quality: Low - No relevant information found")
        return "I don't have enough information in memory to answer that question.", "Low"

def generate_answer(question, results):
    """Generate an answer based on search results"""
    if not results:
        return "I don't have enough information in memory to answer that question."
    
    # Extract information from top result
    top_result = results[0]
    content = top_result.content
    
    # Extract app name, which is often useful for answering PC questions
    app_name = None
    if hasattr(top_result, "metadata") and top_result.metadata and "application_name" in top_result.metadata:
        app_name = top_result.metadata["application_name"]
    
    # Generate different answers based on question type
    if "operating system" in question.lower():
        if "macos" in content.lower() or "darwin" in content.lower():
            return "The computer is running macOS."
        elif "windows" in content.lower():
            return "The computer is running Windows."
        elif "linux" in content.lower() or "ubuntu" in content.lower():
            return "The computer is running Linux."
        else:
            return "I can't determine the operating system from the available memory data."
    
    elif "applications" in question.lower() or "installed" in question.lower():
        # Look for application names across all results
        apps = set()
        for result in results:
            if hasattr(result, "metadata") and result.metadata and "application_name" in result.metadata:
                apps.add(result.metadata["application_name"])
            
            # Also look in content for app names
            content = result.content.lower()
            for app in ["chrome", "firefox", "safari", "vscode", "visual studio code", 
                       "terminal", "spotify", "slack", "word", "excel", "outlook"]:
                if app in content:
                    apps.add(app.title())
        
        if apps:
            return f"The PC has several applications installed including {', '.join(list(apps)[:5])}."
        else:
            return "I can see evidence of application usage but can't identify specific installed applications."
    
    elif "browser" in question.lower():
        browsers = []
        for result in results:
            content = result.content.lower()
            if "chrome" in content:
                browsers.append("Google Chrome")
            elif "firefox" in content:
                browsers.append("Firefox")
            elif "safari" in content:
                browsers.append("Safari")
            elif "edge" in content:
                browsers.append("Microsoft Edge")
            
            if hasattr(result, "metadata") and result.metadata and "application_name" in result.metadata:
                app = result.metadata["application_name"]
                if "chrome" in app.lower():
                    browsers.append("Google Chrome")
                elif "firefox" in app.lower():
                    browsers.append("Firefox")
                elif "safari" in app.lower():
                    browsers.append("Safari")
                elif "edge" in app.lower():
                    browsers.append("Microsoft Edge")
        
        if browsers:
            browsers = list(set(browsers))  # Remove duplicates
            return f"The user is using {browsers[0]} as their browser."
        else:
            return "I can't determine which browser the user is using from the available memory data."
    
    elif "development environment" in question.lower():
        ides = []
        for result in results:
            content = result.content.lower()
            if "vscode" in content or "visual studio code" in content:
                ides.append("Visual Studio Code")
            elif "intellij" in content:
                ides.append("IntelliJ")
            elif "pycharm" in content:
                ides.append("PyCharm")
            elif "eclipse" in content:
                ides.append("Eclipse")
            
            if hasattr(result, "metadata") and result.metadata and "application_name" in result.metadata:
                app = result.metadata["application_name"]
                if "vscode" in app.lower() or "visual studio code" in app.lower():
                    ides.append("Visual Studio Code")
        
        if ides:
            ides = list(set(ides))  # Remove duplicates
            return f"The user prefers {ides[0]} as their development environment."
        else:
            return "I can't determine the user's preferred development environment from the available memory data."
    
    elif "last file" in question.lower() or "file edited" in question.lower():
        files = []
        for result in results:
            content = result.content.lower()
            if ".py" in content or ".js" in content or ".html" in content or ".css" in content or ".txt" in content:
                # Extract filename if present
                words = content.split()
                for word in words:
                    if "." in word and not word.startswith("http"):
                        files.append(word)
            
            if hasattr(result, "metadata") and result.metadata and "file_path" in result.metadata:
                files.append(result.metadata["file_path"].split("/")[-1])
        
        if files:
            return f"The last file the user edited was {files[0]}."
        else:
            return "I can't determine the last file edited from the available memory data."
    
    elif "media" in question.lower():
        media_apps = []
        for result in results:
            content = result.content.lower()
            if "spotify" in content:
                media_apps.append("Spotify")
            elif "netflix" in content:
                media_apps.append("Netflix")
            elif "youtube" in content:
                media_apps.append("YouTube")
            elif "apple music" in content:
                media_apps.append("Apple Music")
            
            if hasattr(result, "metadata") and result.metadata and "application_name" in result.metadata:
                app = result.metadata["application_name"]
                if "spotify" in app.lower():
                    media_apps.append("Spotify")
                elif "youtube" in app.lower():
                    media_apps.append("YouTube")
        
        if media_apps:
            media_apps = list(set(media_apps))  # Remove duplicates
            return f"Yes, the user has been using {media_apps[0]}."
        else:
            return "I don't see evidence of media application usage in the available memory data."
    
    elif "programming languages" in question.lower():
        languages = []
        for result in results:
            content = result.content.lower()
            if "python" in content:
                languages.append("Python")
            elif "javascript" in content:
                languages.append("JavaScript")
            elif "java" in content:
                languages.append("Java")
            elif "c++" in content:
                languages.append("C++")
            elif "typescript" in content:
                languages.append("TypeScript")
        
        if languages:
            languages = list(set(languages))  # Remove duplicates
            return f"The user works with {', '.join(languages)}."
        else:
            return "I can't determine which programming languages the user works with from the available memory data."
    
    elif "websites" in question.lower():
        websites = []
        for result in results:
            content = result.content.lower()
            if "gmail" in content:
                websites.append("Gmail")
            elif "github" in content:
                websites.append("GitHub")
            elif "stack overflow" in content:
                websites.append("Stack Overflow")
            elif "google" in content:
                websites.append("Google")
            
            if hasattr(result, "metadata") and result.metadata and "url" in result.metadata:
                url = result.metadata["url"]
                if "gmail" in url:
                    websites.append("Gmail")
                elif "github" in url:
                    websites.append("GitHub")
                elif "stackoverflow" in url:
                    websites.append("Stack Overflow")
                elif "google" in url:
                    websites.append("Google")
        
        if websites:
            websites = list(set(websites))  # Remove duplicates
            return f"The user frequently visits {', '.join(websites)}."
        else:
            return "I can't determine which websites the user frequently visits from the available memory data."
    
    elif "recent application" in question.lower():
        if app_name:
            return f"The most recent application the user opened was {app_name}."
        else:
            # Try to extract from content
            for app in ["Chrome", "VSCode", "Visual Studio Code", "Terminal", "Spotify", "Slack"]:
                if app.lower() in content.lower():
                    return f"The most recent application the user opened appears to be {app}."
            
            return "I can't determine the most recent application from the available memory data."
    
    elif "projects" in question.lower():
        projects = []
        for result in results:
            content = result.content.lower()
            if "semantic search" in content:
                projects.append("semantic search implementation")
            elif "vector embeddings" in content:
                projects.append("vector embeddings system")
            elif "tf-idf" in content:
                projects.append("TF-IDF document processing")
        
        if projects:
            projects = list(set(projects))  # Remove duplicates
            return f"The user is currently working on a {projects[0]} project."
        else:
            return "I can't determine the user's current projects from the available memory data."
    
    # Default answer based on top result
    return f"Based on the available memory data, {content.lower().replace('user', 'the user')}"

def evaluate_answer_quality(question, answer, results):
    """Evaluate the quality of the generated answer"""
    if not results:
        return "Low - No data available"
    
    # Check if the answer is the default "not enough information" response
    if "don't have enough information" in answer:
        return "Low - Insufficient information"
    
    # Check the similarity score of the top result
    top_similarity = results[0].similarity_score if results else 0
    
    if top_similarity > 0.5:
        return "High - Strong evidence in memory"
    elif top_similarity > 0.3:
        return "Medium - Some relevant information found"
    elif top_similarity > 0.15:
        return "Low-Medium - Weak relevance but some information available"
    else:
        return "Low - Minimal relevance"

async def main():
    """Run the main program"""
    logger.info("🧠 TESTING PC QUESTIONS WITH SEMANTIC SEARCH")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    
    # Track overall results
    quality_counts = {"High": 0, "Medium": 0, "Low-Medium": 0, "Low": 0}
    answers = []
    
    # Run each PC question
    for question in PC_QUESTIONS:
        answer, quality = await search_memory_for_answer(search_agent, question)
        answers.append({"question": question, "answer": answer, "quality": quality})
        
        # Count quality levels
        for level in quality_counts.keys():
            if level in quality:
                quality_counts[level] += 1
    
    # Show summary
    logger.info("\n📊 RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Questions asked: {len(PC_QUESTIONS)}")
    for level, count in quality_counts.items():
        percent = count / len(PC_QUESTIONS) * 100
        logger.info(f"{level} quality answers: {count} ({percent:.1f}%)")
    
    # Final assessment
    high_medium = quality_counts["High"] + quality_counts["Medium"]
    percent_useful = high_medium / len(PC_QUESTIONS) * 100
    
    logger.info("\n🎯 FINAL ASSESSMENT")
    logger.info("=" * 70)
    if percent_useful >= 70:
        logger.info("✅ EXCELLENT: The semantic search provides highly meaningful answers to PC questions")
    elif percent_useful >= 50:
        logger.info("✅ GOOD: The semantic search provides moderately useful answers to PC questions")
    elif percent_useful >= 30:
        logger.info("⚠️ FAIR: The semantic search provides some useful information but with limitations")
    else:
        logger.info("❌ POOR: The semantic search has limited ability to answer PC questions with current memory")
    
    logger.info(f"Overall usefulness: {percent_useful:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())