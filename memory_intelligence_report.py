#!/usr/bin/env python3
"""
Memory Intelligence Report - Show meaningful understanding of user activities
Demonstrates semantic search capabilities and behavioral analysis
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

async def generate_memory_intelligence_report():
    """Generate comprehensive memory intelligence report"""
    
    print("🧠 MEMORY INTELLIGENCE REPORT")
    print("=" * 70)
    print("Analyzing your recent activities and current behavior patterns...")
    print()
    
    # Initialize memory system
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    # Get recent memories (last 5 minutes)
    current_time = time.time()
    five_minutes_ago = current_time - (5 * 60)
    
    print("📊 ACTIVITY ANALYSIS - LAST 5 MINUTES")
    print("=" * 50)
    
    # Analyze short-term memory for recent activities
    recent_activities = []
    if memory_system.short_term_memory:
        for memory_item in memory_system.short_term_memory:
            if isinstance(memory_item, dict) and memory_item.get('timestamp', 0) > five_minutes_ago:
                recent_activities.append(memory_item)
    
    print(f"📝 Found {len(recent_activities)} memory entries from last 5 minutes")
    print()
    
    if recent_activities:
        # Analyze patterns in recent activities
        focus_scores = []
        productivity_scores = []
        intents = []
        workflow_stages = []
        
        for activity in recent_activities:
            user_behavior = activity.get('user_behavior', {})
            
            if user_behavior:
                focus_level = user_behavior.get('focus_level', {})
                productivity = user_behavior.get('productivity_indicator', {})
                
                focus_scores.append(focus_level.get('focus_score', 0))
                productivity_scores.append(productivity.get('productivity_score', 0))
                intents.append(user_behavior.get('inferred_intent', 'unknown'))
                workflow_stages.append(user_behavior.get('workflow_stage', 'unknown'))
        
        # Calculate insights
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        avg_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0
        most_common_intent = max(set(intents), key=intents.count) if intents else 'unknown'
        most_common_stage = max(set(workflow_stages), key=workflow_stages.count) if workflow_stages else 'unknown'
        
        print("🎯 BEHAVIORAL INSIGHTS:")
        print(f"   Average Focus Level: {avg_focus:.2f}/1.0 ({('🔴 Low', '🟡 Medium', '🟢 High')[int(avg_focus * 3) if avg_focus < 1 else 2]})")
        print(f"   Average Productivity: {avg_productivity:.2f}/1.0 ({('📉 Low', '📊 Medium', '📈 High')[int(avg_productivity * 3) if avg_productivity < 1 else 2]})")
        print(f"   Primary Intent: {most_common_intent}")
        print(f"   Workflow Stage: {most_common_stage}")
        print()
        
        # Analyze most recent activity (current state)
        latest_activity = recent_activities[-1] if recent_activities else None
        if latest_activity:
            print("🔍 CURRENT ACTIVITY ANALYSIS:")
            user_behavior = latest_activity.get('user_behavior', {})
            active_apps = latest_activity.get('active_applications', {}).get('foreground', [])
            visual_context = latest_activity.get('visual_context', {})
            file_context = latest_activity.get('file_context', {})
            
            print(f"   Current Intent: {user_behavior.get('inferred_intent', 'unknown')}")
            print(f"   Confidence: {user_behavior.get('confidence', 0):.1%}")
            print(f"   Activity Type: {user_behavior.get('activity_type', 'unknown')}")
            print(f"   Focus Score: {user_behavior.get('focus_level', {}).get('focus_score', 0):.2f}")
            
            # Show active applications
            if active_apps:
                print(f"   Active Applications:")
                for app in active_apps[:3]:  # Show top 3
                    app_name = app.get('name', 'Unknown')
                    app_type = app.get('type', 'unknown')
                    relevance = app.get('context_relevance', 0)
                    print(f"     • {app_name} ({app_type}) - Relevance: {relevance:.1f}")
            
            # Show file context if available
            current_file = file_context.get('current_file', {})
            if current_file:
                file_path = current_file.get('path', 'Unknown')
                file_type = current_file.get('type', 'unknown')
                print(f"   Current File: {os.path.basename(file_path)} ({file_type})")
                
                file_patterns = file_context.get('file_patterns', {})
                if file_patterns:
                    project_type = file_patterns.get('project_type', 'unknown')
                    dev_stage = file_patterns.get('development_stage', 'unknown')
                    print(f"   Project Context: {project_type} - {dev_stage}")
            
            print()
    else:
        print("ℹ️  No recent activity found in last 5 minutes")
        print()
    
    # Current state analysis
    print("🎯 CURRENT STATE ANALYSIS")
    print("=" * 40)
    
    current_context = memory_system.context_memory.get('current_context', {})
    if current_context:
        user_behavior = current_context.get('user_behavior', {})
        
        print("🧠 COGNITIVE STATE:")
        focus_level = user_behavior.get('focus_level', {})
        print(f"   Attention Type: {focus_level.get('attention_type', 'unknown')}")
        
        flow_indicators = focus_level.get('flow_state_indicators', [])
        if flow_indicators:
            print(f"   Flow Indicators: {', '.join(flow_indicators)}")
        
        distraction_indicators = focus_level.get('distraction_indicators', [])
        if distraction_indicators:
            print(f"   Distractions: {', '.join(distraction_indicators)}")
        
        productivity = user_behavior.get('productivity_indicator', {})
        prod_indicators = productivity.get('indicators', [])
        if prod_indicators:
            print(f"   Productivity Factors: {', '.join(prod_indicators)}")
        
        blockers = productivity.get('blockers', [])
        if blockers:
            print(f"   Productivity Blockers: {', '.join(blockers)}")
    else:
        print("ℹ️  No current context available")
    
    print()
    
    # Demonstrate semantic search capabilities
    print("🔍 SEMANTIC SEARCH CAPABILITIES DEMONSTRATION")
    print("=" * 55)
    
    search_queries = [
        "memory system development",
        "testing and debugging activities", 
        "Python programming work",
        "focus and productivity patterns",
        "file editing and code work"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Searching: '{query}'")
        print("-" * 40)
        
        try:
            # Use the enhanced semantic search
            search_results = memory_system.semantic_search.search(query, limit=3)
            
            if search_results:
                print(f"   Found {len(search_results)} relevant memories:")
                
                for i, result in enumerate(search_results, 1):
                    # Extract meaningful information from search result
                    if isinstance(result, dict):
                        # Check if it's a memory item with our enhanced structure
                        if 'user_behavior' in result:
                            user_behavior = result['user_behavior']
                            intent = user_behavior.get('inferred_intent', 'unknown')
                            activity_type = user_behavior.get('activity_type', 'unknown')
                            significance = user_behavior.get('significance_score', 0)
                            
                            timestamp = result.get('timestamp', time.time())
                            time_ago = (time.time() - timestamp) / 60  # minutes ago
                            
                            print(f"     {i}. {intent} ({activity_type}) - {significance:.1f} significance")
                            print(f"        {time_ago:.1f} minutes ago")
                            
                            # Show relevant apps or files
                            apps = result.get('active_applications', {}).get('foreground', [])
                            if apps:
                                app_name = apps[0].get('name', 'Unknown') if apps else 'None'
                                print(f"        App: {app_name}")
                            
                            file_context = result.get('file_context', {})
                            current_file = file_context.get('current_file', {})
                            if current_file:
                                file_name = os.path.basename(current_file.get('path', 'Unknown'))
                                print(f"        File: {file_name}")
                        else:
                            # Fallback for other memory types
                            content = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                            print(f"     {i}. {content}")
                    else:
                        content = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                        print(f"     {i}. {content}")
            else:
                print("   No relevant memories found")
                
        except Exception as e:
            print(f"   Search error: {e}")
    
    # Memory system health check
    print(f"\n📊 MEMORY SYSTEM HEALTH")
    print("=" * 30)
    
    short_term_count = len(memory_system.short_term_memory)
    long_term_count = len(memory_system.long_term_memory) 
    context_keys = len(memory_system.context_memory.keys()) if isinstance(memory_system.context_memory, dict) else 0
    
    print(f"Short-term Memory: {short_term_count} items")
    print(f"Long-term Memory: {long_term_count} items") 
    print(f"Context Memory: {context_keys} keys")
    print(f"Conscious Memory: {'✅ Active' if hasattr(memory_system, 'conscious_memory') else '❌ Inactive'}")
    print(f"Enhanced Understanding: {'✅ Enabled' if hasattr(memory_system, '_analyze_user_intent') else '❌ Disabled'}")
    
    # Summary insights
    print(f"\n🎯 KEY INSIGHTS SUMMARY")
    print("=" * 30)
    
    if recent_activities:
        total_focus_time = sum(1 for score in focus_scores if score > 0.7)
        total_productive_time = sum(1 for score in productivity_scores if score > 0.5)
        
        print(f"High Focus Sessions: {total_focus_time}/{len(focus_scores)}")
        print(f"Productive Sessions: {total_productive_time}/{len(productivity_scores)}")
        print(f"Primary Work Type: {most_common_intent}")
        print(f"Workflow Consistency: {workflow_stages.count(most_common_stage)}/{len(workflow_stages)} in same stage")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_focus < 0.5:
            print("   • Consider reducing distractions to improve focus")
        if avg_productivity < 0.5:
            print("   • Review current activities for productivity optimization")
        if len(set(intents)) > 3:
            print("   • High task switching detected - consider time blocking")
        if avg_focus > 0.8 and avg_productivity > 0.6:
            print("   • ✅ Excellent focus and productivity! Keep up the great work!")
    
    print(f"\n📄 Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function to generate memory intelligence report"""
    try:
        await generate_memory_intelligence_report()
    except Exception as e:
        print(f"❌ Error generating memory report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())