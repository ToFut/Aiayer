#!/usr/bin/env python3
"""
Add Test Memories
Adds test memories to the system to validate semantic search
"""
import sys
import os
import asyncio
import logging
import json
from datetime import datetime

# Add parent directory to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import the memory system
try:
    from memory.memory_system import MemorySystem
except ImportError as e:
    logger.error(f"Error importing memory modules: {e}")
    sys.exit(1)

async def add_test_memories():
    """Add test memories to the system."""
    try:
        print("🧠 Initializing memory system...")
        memory = MemorySystem()
        print(f"✅ Memory system initialized with {len(memory.short_term_memory)} short-term memories")
        
        # Test memories covering various topics with professional context
        test_memories = [
            {
                "content": "User working on coding a Python application with complex data structures",
                "memory_type": "professional_activity",
                "user_activity": {
                    "primary_activity": "development",
                    "application_used": "Cursor",
                    "professional_context": "software_engineering",
                    "workflow_stage": "active_coding",
                    "productivity_score": 0.85
                },
                "context_analysis": {
                    "workflow_stage": "development",
                    "meaningful_interaction": True
                },
                "insights": ["Python development", "Software engineering workflow"]
            },
            {
                "content": "Researching semantic search algorithms and vector embeddings for improved memory recall",
                "memory_type": "research_activity",
                "user_activity": {
                    "primary_activity": "research",
                    "application_used": "Chrome",
                    "professional_context": "technical_research",
                    "workflow_stage": "information_gathering",
                    "productivity_score": 0.75
                },
                "context_analysis": {
                    "workflow_stage": "research",
                    "meaningful_interaction": True
                },
                "insights": ["AI research", "Semantic search technology"]
            },
            {
                "content": "Memory system architecture review focusing on scalability and performance",
                "memory_type": "architecture_analysis",
                "user_activity": {
                    "primary_activity": "architecture",
                    "application_used": "Draw.io",
                    "professional_context": "system_design",
                    "workflow_stage": "design_review",
                    "productivity_score": 0.9
                },
                "context_analysis": {
                    "workflow_stage": "architecture",
                    "meaningful_interaction": True
                },
                "insights": ["System architecture", "Design patterns", "Scalability"]
            },
            {
                "content": "Debugging memory integration issues in log traces with performance bottlenecks",
                "memory_type": "debugging_session",
                "user_activity": {
                    "primary_activity": "debugging",
                    "application_used": "Terminal",
                    "professional_context": "troubleshooting",
                    "workflow_stage": "problem_solving",
                    "productivity_score": 0.8
                },
                "context_analysis": {
                    "workflow_stage": "debugging",
                    "meaningful_interaction": True
                },
                "insights": ["Performance optimization", "Error handling", "Log analysis"]
            },
            {
                "content": "Testing vector similarity search with comprehensive validation cases",
                "memory_type": "testing_activity",
                "user_activity": {
                    "primary_activity": "testing",
                    "application_used": "VS Code",
                    "professional_context": "quality_assurance",
                    "workflow_stage": "validation",
                    "productivity_score": 0.85
                },
                "context_analysis": {
                    "workflow_stage": "testing",
                    "meaningful_interaction": True
                },
                "insights": ["Test validation", "Search functionality", "Quality assurance"]
            },
            {
                "content": "AI embeddings model evaluation comparing performance across different dimensionality",
                "memory_type": "ai_research",
                "user_activity": {
                    "primary_activity": "research",
                    "application_used": "Jupyter",
                    "professional_context": "data_science",
                    "workflow_stage": "experimentation",
                    "productivity_score": 0.9
                },
                "context_analysis": {
                    "workflow_stage": "research",
                    "meaningful_interaction": True
                },
                "insights": ["AI models", "Vector embeddings", "Performance evaluation"]
            },
            {
                "content": "Implementing hybrid retrieval with token-based and vector similarity search",
                "memory_type": "implementation",
                "user_activity": {
                    "primary_activity": "development",
                    "application_used": "Cursor",
                    "professional_context": "software_engineering",
                    "workflow_stage": "implementation",
                    "productivity_score": 0.85
                },
                "context_analysis": {
                    "workflow_stage": "development",
                    "meaningful_interaction": True
                },
                "insights": ["Hybrid search", "Algorithm development", "Information retrieval"]
            },
            {
                "content": "Optimizing memory retrieval with context-aware filtering and relevance boosting",
                "memory_type": "optimization",
                "user_activity": {
                    "primary_activity": "optimization",
                    "application_used": "VS Code",
                    "professional_context": "performance_tuning",
                    "workflow_stage": "refinement",
                    "productivity_score": 0.8
                },
                "context_analysis": {
                    "workflow_stage": "optimization",
                    "meaningful_interaction": True
                },
                "insights": ["Performance tuning", "Search relevance", "Context awareness"]
            }
        ]
        
        # Add memories
        success_count = 0
        for i, memory_data in enumerate(test_memories):
            try:
                # Add to memory system
                memory_id = await memory.add_to_short_term_memory(memory_data)
                
                if memory_id:
                    success_count += 1
                    print(f"  ✅ Added memory {i+1}: {memory_data['content'][:50]}...")
                else:
                    print(f"  ❌ Failed to add memory {i+1}")
                    
            except Exception as e:
                logger.error(f"Error adding memory {i+1}: {e}")
        
        # Save memory state
        await memory.save_memory_state()
        
        # Final report
        print(f"\n✅ Added {success_count}/{len(test_memories)} test memories")
        print(f"Current memory count: {len(memory.short_term_memory)} short-term memories")
        
        return success_count
        
    except Exception as e:
        logger.error(f"Error in add_test_memories: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    asyncio.run(add_test_memories())