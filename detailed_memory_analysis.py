#!/usr/bin/env python3
"""
Detailed Memory Analysis - Show what the memory system actually remembers
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

async def analyze_detailed_memories():
    """Analyze detailed memories and show understanding"""
    
    print("🔍 DETAILED MEMORY ANALYSIS - WHAT I REMEMBER ABOUT YOU")
    print("=" * 70)
    
    # Initialize memory system
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    print(f"📊 Memory Statistics:")
    print(f"   Short-term: {len(memory_system.short_term_memory)} memories")
    print(f"   Context keys: {len(memory_system.context_memory.keys())}")
    print()
    
    # Analyze short-term memories in detail
    print("🧠 SHORT-TERM MEMORY ANALYSIS")
    print("=" * 40)
    
    if memory_system.short_term_memory:
        print(f"📝 Analyzing {len(memory_system.short_term_memory)} memory entries...")
        print()
        
        # Show the most recent 3 memories in detail
        recent_memories = memory_system.short_term_memory[-3:] if len(memory_system.short_term_memory) >= 3 else memory_system.short_term_memory
        
        for i, memory in enumerate(recent_memories, 1):
            if isinstance(memory, dict):
                timestamp = memory.get('timestamp', time.time())
                time_ago = (time.time() - timestamp) / 60  # minutes ago
                
                print(f"📋 MEMORY ENTRY #{i} ({time_ago:.1f} minutes ago)")
                print("-" * 30)
                
                # User behavior analysis
                user_behavior = memory.get('user_behavior', {})
                if user_behavior:
                    print("🧠 BEHAVIORAL UNDERSTANDING:")
                    print(f"   Intent: {user_behavior.get('inferred_intent', 'unknown')}")
                    print(f"   Confidence: {user_behavior.get('confidence', 0):.1%}")
                    print(f"   Activity Type: {user_behavior.get('activity_type', 'unknown')}")
                    print(f"   Workflow Stage: {user_behavior.get('workflow_stage', 'unknown')}")
                    print(f"   Significance: {user_behavior.get('significance_score', 0):.2f}/1.0")
                    
                    focus_level = user_behavior.get('focus_level', {})
                    if focus_level:
                        print(f"   Focus Score: {focus_level.get('focus_score', 0):.2f}/1.0")
                        print(f"   Attention Type: {focus_level.get('attention_type', 'unknown')}")
                        
                        flow_indicators = focus_level.get('flow_state_indicators', [])
                        if flow_indicators:
                            print(f"   Flow State: {', '.join(flow_indicators)}")
                        
                        distractions = focus_level.get('distraction_indicators', [])
                        if distractions:
                            print(f"   Distractions: {', '.join(distractions)}")
                    
                    productivity = user_behavior.get('productivity_indicator', {})
                    if productivity:
                        print(f"   Productivity: {productivity.get('productivity_score', 0):.2f}/1.0")
                        
                        indicators = productivity.get('indicators', [])
                        if indicators:
                            print(f"   Positive Factors: {', '.join(indicators)}")
                        
                        blockers = productivity.get('blockers', [])
                        if blockers:
                            print(f"   Blockers: {', '.join(blockers)}")
                
                # Application context
                apps = memory.get('active_applications', {})
                foreground_apps = apps.get('foreground', [])
                if foreground_apps:
                    print(f"\n💻 APPLICATIONS IN USE:")
                    for app in foreground_apps[:3]:  # Show top 3
                        app_name = app.get('name', 'Unknown')
                        app_type = app.get('type', 'unknown')
                        app_category = app.get('category', 'unknown')
                        relevance = app.get('context_relevance', 0)
                        usage_pattern = app.get('usage_pattern', {})
                        
                        print(f"   • {app_name}")
                        print(f"     Type: {app_type} | Category: {app_category}")
                        print(f"     Relevance: {relevance:.1f} | Context: {usage_pattern.get('context_association', [])}")
                
                # File context
                file_context = memory.get('file_context', {})
                if file_context:
                    current_file = file_context.get('current_file', {})
                    if current_file:
                        print(f"\n📁 FILE CONTEXT:")
                        file_path = current_file.get('path', 'Unknown')
                        file_type = current_file.get('type', 'unknown')
                        file_size = current_file.get('size', 0)
                        
                        print(f"   Current File: {os.path.basename(file_path)}")
                        print(f"   Type: {file_type} | Size: {file_size} bytes")
                        print(f"   Full Path: {file_path}")
                        
                        file_patterns = file_context.get('file_patterns', {})
                        if file_patterns:
                            project_type = file_patterns.get('project_type', 'unknown')
                            dev_stage = file_patterns.get('development_stage', 'unknown')
                            collaboration = file_patterns.get('collaboration_indicators', [])
                            
                            print(f"   Project Type: {project_type}")
                            print(f"   Development Stage: {dev_stage}")
                            if collaboration:
                                print(f"   Collaboration: {', '.join(collaboration)}")
                    
                    recent_files = file_context.get('recent_files', [])
                    if recent_files:
                        print(f"   Recent Files: {len(recent_files)} files")
                        for file_info in recent_files[:3]:
                            file_name = os.path.basename(file_info.get('path', 'Unknown'))
                            print(f"     • {file_name}")
                
                # Visual context
                visual_context = memory.get('visual_context', {})
                if visual_context:
                    active_window = visual_context.get('active_window', {})
                    if active_window:
                        print(f"\n👁️ VISUAL CONTEXT:")
                        window_title = active_window.get('title', 'Unknown')
                        window_app = active_window.get('application', 'Unknown')
                        print(f"   Active Window: {window_title}")
                        print(f"   Application: {window_app}")
                    
                    ui_elements = visual_context.get('ui_elements', {})
                    if ui_elements:
                        controls = len(ui_elements.get('controls', []))
                        text_fields = len(ui_elements.get('text_fields', []))
                        navigation = len(ui_elements.get('navigation', []))
                        print(f"   UI Elements: {controls} controls, {text_fields} text fields, {navigation} nav items")
                    
                    text_content = visual_context.get('text_content', {})
                    if text_content:
                        content_type = text_content.get('content_type', 'unknown')
                        topics = text_content.get('semantic_topics', [])
                        print(f"   Content Type: {content_type}")
                        if topics:
                            print(f"   Topics: {', '.join(topics)}")
                
                print(f"\n" + "="*50 + "\n")
    
    # Current context analysis
    print("🎯 CURRENT CONTEXT UNDERSTANDING")
    print("=" * 40)
    
    current_context = memory_system.context_memory.get('current_context', {})
    if current_context:
        print("🧠 WHAT I UNDERSTAND RIGHT NOW:")
        
        user_behavior = current_context.get('user_behavior', {})
        if user_behavior:
            intent = user_behavior.get('inferred_intent', 'unknown')
            confidence = user_behavior.get('confidence', 0)
            activity_type = user_behavior.get('activity_type', 'unknown')
            workflow_stage = user_behavior.get('workflow_stage', 'unknown')
            
            print(f"   You are: {intent} ({activity_type})")
            print(f"   Confidence: {confidence:.1%}")
            print(f"   Workflow Stage: {workflow_stage}")
            
            focus_level = user_behavior.get('focus_level', {})
            if focus_level:
                focus_score = focus_level.get('focus_score', 0)
                attention_type = focus_level.get('attention_type', 'unknown')
                print(f"   Focus Level: {focus_score:.1%} ({attention_type})")
            
            productivity = user_behavior.get('productivity_indicator', {})
            if productivity:
                prod_score = productivity.get('productivity_score', 0)
                print(f"   Productivity: {prod_score:.1%}")
    
    # Semantic search demonstration with actual queries
    print("🔍 SEMANTIC SEARCH DEMONSTRATION")
    print("=" * 40)
    
    print("Let me search through my memories about you...")
    print()
    
    # Test specific queries about user behavior
    test_queries = [
        "development work",
        "memory system",
        "focus and concentration",
        "Python programming",
        "testing activities"
    ]
    
    for query in test_queries:
        print(f"🔎 Searching for: '{query}'")
        try:
            results = memory_system.semantic_search.search(query, limit=2)
            if results and len(results) > 0:
                print(f"   ✅ Found {len(results)} relevant memories")
                
                for i, result in enumerate(results, 1):
                    if isinstance(result, dict):
                        # Look for meaningful data
                        if 'user_behavior' in result:
                            behavior = result['user_behavior']
                            intent = behavior.get('inferred_intent', 'unknown')
                            activity = behavior.get('activity_type', 'unknown')
                            confidence = behavior.get('confidence', 0)
                            
                            print(f"     {i}. {intent} activity ({activity}) - {confidence:.1%} confidence")
                        elif 'content' in str(result):
                            content = str(result)[:80] + "..." if len(str(result)) > 80 else str(result)
                            print(f"     {i}. {content}")
                        else:
                            print(f"     {i}. Memory entry with {len(result)} fields")
            else:
                print(f"   ℹ️ No specific memories found for '{query}'")
        except Exception as e:
            print(f"   ⚠️ Search error: {e}")
        print()
    
    # Memory insights summary
    print("💡 MEMORY INSIGHTS SUMMARY")
    print("=" * 30)
    
    if memory_system.short_term_memory:
        # Analyze patterns across all memories
        all_intents = []
        all_focus_scores = []
        all_productivity_scores = []
        all_activities = []
        
        for memory in memory_system.short_term_memory:
            if isinstance(memory, dict):
                user_behavior = memory.get('user_behavior', {})
                if user_behavior:
                    all_intents.append(user_behavior.get('inferred_intent', 'unknown'))
                    all_activities.append(user_behavior.get('activity_type', 'unknown'))
                    
                    focus_level = user_behavior.get('focus_level', {})
                    if focus_level:
                        all_focus_scores.append(focus_level.get('focus_score', 0))
                    
                    productivity = user_behavior.get('productivity_indicator', {})
                    if productivity:
                        all_productivity_scores.append(productivity.get('productivity_score', 0))
        
        print("📊 PATTERN ANALYSIS:")
        if all_intents:
            from collections import Counter
            intent_counts = Counter(all_intents)
            most_common_intent = intent_counts.most_common(1)[0]
            print(f"   Most common activity: {most_common_intent[0]} ({most_common_intent[1]} times)")
        
        if all_focus_scores:
            avg_focus = sum(all_focus_scores) / len(all_focus_scores)
            print(f"   Average focus level: {avg_focus:.2f}/1.0")
            high_focus_sessions = sum(1 for score in all_focus_scores if score > 0.7)
            print(f"   High focus sessions: {high_focus_sessions}/{len(all_focus_scores)}")
        
        if all_productivity_scores:
            avg_productivity = sum(all_productivity_scores) / len(all_productivity_scores)
            print(f"   Average productivity: {avg_productivity:.2f}/1.0")
        
        print(f"\n🎯 BEHAVIORAL CONCLUSION:")
        if avg_focus > 0.7 and avg_productivity > 0.6:
            print("   You maintain excellent focus and productivity while working!")
        elif avg_focus > 0.5:
            print("   You show good focus patterns with room for optimization")
        else:
            print("   Your work patterns suggest potential for focus improvement")
    
    print(f"\n📄 Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function"""
    try:
        await analyze_detailed_memories()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())