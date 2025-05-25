#!/usr/bin/env python3
"""
Search Memory for UI Understanding Insights
Find specific UI analysis and deep insights stored in memory
"""

import json
import os
from datetime import datetime
from pathlib import Path

def search_ui_memory_insights():
    """Search for UI understanding insights in memory"""
    print("\n" + "="*80)
    print("🔍 SEARCHING MEMORY FOR UI UNDERSTANDING INSIGHTS")
    print("="*80)
    
    # Search main memory file
    memory_file = Path("memory/memory/memory_state.json")
    if memory_file.exists():
        print(f"📂 Searching: {memory_file}")
        with open(memory_file, 'r') as f:
            memory_data = json.load(f)
        
        search_memory_for_ui_insights(memory_data)
    
    # Search cache files
    search_cache_for_ui_insights()
    
    # Search logs for UI activities
    search_logs_for_ui_insights()

def search_memory_for_ui_insights(memory_data):
    """Search memory data for UI insights"""
    print(f"\n🧠 MEMORY DATA ANALYSIS:")
    print("="*50)
    
    # Search short-term memory
    short_term = memory_data.get("short_term", [])
    print(f"📋 Short-term memory entries: {len(short_term)}")
    
    ui_insights_found = 0
    professional_contexts = 0
    saas_platforms = 0
    complex_uis = 0
    
    for i, entry in enumerate(short_term):
        print(f"\n📝 Entry {i+1}:")
        timestamp = entry.get("timestamp", 0)
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            print(f"   ⏰ Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check for UI analysis
        if "ui_analysis" in entry:
            ui_insights_found += 1
            ui_analysis = entry["ui_analysis"]
            print(f"   🎛️ UI Analysis Found!")
            
            if "ui_elements" in ui_analysis:
                elements = ui_analysis["ui_elements"]
                total_elements = sum(len(subcat) for cat in elements.values() for subcat in cat.values())
                print(f"      • UI Elements: {total_elements} detected")
                for category, subcats in elements.items():
                    if subcats:
                        count = sum(len(subcat) for subcat in subcats.values())
                        print(f"        - {category.title()}: {count}")
            
            if "saas_platform" in ui_analysis and ui_analysis["saas_platform"]:
                saas_platforms += 1
                platform = ui_analysis["saas_platform"]
                print(f"      • SaaS Platform: {platform['platform'].title()}")
                print(f"        Confidence: {platform['confidence']:.1%}")
                print(f"        Elements: {', '.join(platform['matched_elements'][:3])}")
            
            if "visualizations" in ui_analysis:
                viz_count = len(ui_analysis["visualizations"])
                print(f"      • Visualizations: {viz_count} detected")
                for viz in ui_analysis["visualizations"][:2]:
                    print(f"        - {viz['type'].replace('_', ' ').title()}: {viz['confidence']:.0%}")
            
            if "ui_complexity_score" in ui_analysis:
                complexity = ui_analysis["ui_complexity_score"]
                print(f"      • UI Complexity: {complexity:.0%}")
                if complexity > 0.7:
                    complex_uis += 1
        
        # Check for complete UI analysis
        if "memory_type" in entry and "complete_ui_analysis" in entry["memory_type"]:
            print(f"   🚀 Complete UI Understanding Entry!")
            if "ui_understanding" in entry:
                understanding = entry["ui_understanding"]
                print(f"      • Elements Detected: {understanding.get('detected_elements', 0)}")
                print(f"      • Platform: {understanding.get('platform_identified', 'None')}")
                print(f"      • Complexity: {understanding.get('complexity_level', 'Unknown')}")
                print(f"      • Usability Score: {understanding.get('usability_score', 0):.0%}")
        
        # Check for professional context
        if "professional_context" in entry:
            professional_contexts += 1
            context = entry["professional_context"]
            print(f"   🏢 Professional Context:")
            print(f"      • Activity: {context.get('activity_type', 'Unknown')}")
            print(f"      • Domain: {', '.join(context.get('domain_expertise', []))}")
            print(f"      • Productivity: {len(context.get('productivity_indicators', []))}/10")
        
        # Check for behavioral analysis
        if "user_behavior" in entry:
            behavior = entry["user_behavior"]
            print(f"   🧠 User Behavior Analysis:")
            print(f"      • Intent: {behavior.get('inferred_intent', 'Unknown')}")
            print(f"      • Workflow Stage: {behavior.get('workflow_stage', 'Unknown')}")
            print(f"      • Activity Type: {behavior.get('activity_type', 'Unknown')}")
            
            if "focus_level" in behavior:
                focus = behavior["focus_level"]
                print(f"      • Focus Score: {focus.get('focus_score', 0):.0%}")
                print(f"      • Attention Type: {focus.get('attention_type', 'Unknown')}")
            
            if "productivity_indicator" in behavior:
                productivity = behavior["productivity_indicator"]
                print(f"      • Productivity Score: {productivity.get('productivity_score', 0):.0%}")
        
        # Check for visual context
        if "visual_context" in entry:
            visual = entry["visual_context"]
            print(f"   👁️ Visual Context:")
            
            if "active_window" in visual:
                window = visual["active_window"]
                print(f"      • Window: {window.get('title', 'Unknown')}")
                print(f"      • App: {window.get('application', 'Unknown')}")
            
            if "content_analysis" in visual:
                content = visual["content_analysis"]
                print(f"      • Content Type: {content.get('content_type', 'Unknown')}")
                print(f"      • Complexity: {content.get('complexity', 'Unknown')}")
                print(f"      • Engagement: {content.get('engagement_level', 0):.1%}")
            
            if "ui_elements" in visual:
                ui_elem = visual["ui_elements"]
                print(f"      • Controls: {ui_elem.get('controls', 0)}")
                print(f"      • Text Fields: {ui_elem.get('text_fields', 0)}")
                print(f"      • Navigation: {ui_elem.get('navigation', 0)}")
        
        # Check for applications
        if "active_applications" in entry:
            apps = entry["active_applications"]
            if "foreground" in apps and apps["foreground"]:
                fg_app = apps["foreground"][0]
                print(f"   💻 Active Application:")
                print(f"      • Name: {fg_app.get('name', 'Unknown')}")
                print(f"      • Type: {fg_app.get('type', 'Unknown')}")
                print(f"      • Category: {fg_app.get('category', 'Unknown')}")
                print(f"      • Context Relevance: {fg_app.get('context_relevance', 0):.0%}")
    
    # Summary
    print(f"\n📊 UI INSIGHTS SUMMARY:")
    print("="*30)
    print(f"   🎯 UI Analysis Entries: {ui_insights_found}")
    print(f"   🏢 Professional Contexts: {professional_contexts}")
    print(f"   🔧 SaaS Platforms Detected: {saas_platforms}")
    print(f"   🎛️ Complex UIs Analyzed: {complex_uis}")
    print(f"   📋 Total Memory Entries: {len(short_term)}")

def search_cache_for_ui_insights():
    """Search cache for UI insights"""
    print(f"\n💾 CACHE ANALYSIS:")
    print("="*30)
    
    # Check app detection cache
    app_cache = Path("cache/app_detection/last_detection.json")
    if app_cache.exists():
        try:
            with open(app_cache, 'r') as f:
                detection = json.load(f)
            print(f"📱 App Detection:")
            print(f"   • App: {detection.get('application', 'Unknown')}")
            print(f"   • Confidence: {detection.get('confidence', 0):.0%}")
            print(f"   • Activity: {detection.get('activity', 'Unknown')}")
            if 'ui_elements' in detection:
                print(f"   • UI Elements: {detection['ui_elements']}")
        except Exception as e:
            print(f"   ⚠️ Error reading app detection: {e}")
    
    # Check LLaVA processor cache
    llava_cache = Path("cache/llava_processor")
    if llava_cache.exists():
        json_files = list(llava_cache.glob("*.json"))
        print(f"\n🖼️ Visual Analysis Cache: {len(json_files)} files")
        
        for json_file in json_files[-2:]:  # Show last 2
            try:
                with open(json_file, 'r') as f:
                    analysis = json.load(f)
                print(f"   📄 {json_file.name}:")
                if 'description' in analysis:
                    print(f"      Description: {analysis['description'][:60]}...")
                if 'ui_elements' in analysis:
                    print(f"      UI Elements: {analysis['ui_elements']}")
                if 'activity_type' in analysis:
                    print(f"      Activity: {analysis['activity_type']}")
            except Exception as e:
                print(f"      ⚠️ Error: {e}")

def search_logs_for_ui_insights():
    """Search logs for UI activity"""
    print(f"\n📜 LOG ANALYSIS:")
    print("="*25)
    
    log_files = [
        "logs/memory_system.log",
        "logs/memory/direct_integration.log"
    ]
    
    ui_keywords = [
        "ui_analysis", "complete_ui", "ui_elements", "saas_platform",
        "visualizations", "professional_context", "user_behavior"
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                ui_related_logs = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in ui_keywords):
                        ui_related_logs.append(line.strip())
                
                if ui_related_logs:
                    print(f"📜 {log_file}: {len(ui_related_logs)} UI-related entries")
                    for log in ui_related_logs[-3:]:  # Show last 3
                        parts = log.split(' - ')
                        if len(parts) >= 3:
                            timestamp = parts[0][-8:]  # Last 8 chars (time)
                            message = parts[-1][:50] + "..." if len(parts[-1]) > 50 else parts[-1]
                            print(f"   {timestamp}: {message}")
                else:
                    print(f"📜 {log_file}: No UI-specific logs found")
                    
            except Exception as e:
                print(f"   ⚠️ Error reading {log_file}: {e}")

def show_memory_access_commands():
    """Show commands to access memory"""
    print(f"\n🛠️ MEMORY ACCESS COMMANDS:")
    print("="*40)
    print("💡 To access memory programmatically:")
    print()
    print("1. 📖 Read memory state:")
    print("   python -c \"import json; print(json.dumps(json.load(open('memory/memory/memory_state.json')), indent=2)[:1000])\"")
    print()
    print("2. 🔍 Search semantic memory:")
    print("   python -c \"from memory.enhanced_semantic_search import EnhancedSemanticSearch; search = EnhancedSemanticSearch(); results = search.search('UI analysis')[:3]; print(results)\"")
    print()
    print("3. 🧠 Query conscious memory:")
    print("   python -c \"import json; print(json.dumps(json.load(open('memory/conscious.json')), indent=2))\"")
    print()
    print("4. 📊 Memory statistics:")
    print("   python -c \"from memory.memory_system import MemorySystem; ms = MemorySystem(); print(f'Short-term: {len(ms.short_term_memory)}, Context: {len(ms.context_memory)}')\"")

if __name__ == "__main__":
    search_ui_memory_insights()
    show_memory_access_commands()