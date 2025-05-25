#!/usr/bin/env python3
"""
Memory Insights Viewer
Shows all generated memory data and deep insights from the UI understanding system
"""

import json
import os
from datetime import datetime
from pathlib import Path

def view_all_memory_insights():
    """View all memory insights and data"""
    print("\n" + "="*80)
    print("🧠 COMPREHENSIVE MEMORY INSIGHTS VIEWER")
    print("="*80)
    print("📍 Showing all generated memory data and deep UI understanding insights")
    
    memory_locations = [
        ("Main Memory State", "memory/memory_state.json"),
        ("Conscious Memory", "memory/conscious.json"),
        ("Conversation History", "memory/conversation_history.json"),
        ("Last Context", "memory/last_context.json"),
        ("Memory Directory", "memory/memory/memory_state.json")
    ]
    
    cache_locations = [
        ("Complete UI Analysis", "cache/complete_ui_understanding/"),
        ("App Detection", "cache/app_detection/"),
        ("Process Sensor", "cache/process_sensor/"),
        ("LLaVA Processor", "cache/llava_processor/")
    ]
    
    print("\n📂 MEMORY STORAGE LOCATIONS:")
    print("="*60)
    
    for name, path in memory_locations:
        full_path = Path(path)
        if full_path.exists():
            if full_path.is_file():
                size = full_path.stat().st_size
                modified = datetime.fromtimestamp(full_path.stat().st_mtime)
                print(f"✅ {name}: {path}")
                print(f"   Size: {size:,} bytes | Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Show summary of content
                try:
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                        show_memory_summary(data, name)
                except Exception as e:
                    print(f"   ⚠️ Error reading: {e}")
            else:
                print(f"✅ {name}: {path} (directory)")
        else:
            print(f"❌ {name}: {path} (not found)")
        print()
    
    print("\n📁 CACHE STORAGE LOCATIONS:")
    print("="*60)
    
    for name, path in cache_locations:
        full_path = Path(path)
        if full_path.exists():
            if full_path.is_dir():
                files = list(full_path.glob("*"))
                print(f"✅ {name}: {path}")
                print(f"   Files: {len(files)} items")
                for file in files[:5]:  # Show first 5 files
                    size = file.stat().st_size if file.is_file() else "dir"
                    print(f"     • {file.name} ({size})")
                if len(files) > 5:
                    print(f"     ... and {len(files) - 5} more")
            else:
                print(f"✅ {name}: {path} (file)")
        else:
            print(f"❌ {name}: {path} (not found)")
        print()
    
    # Show recent UI understanding insights
    show_recent_ui_insights()
    
    # Show memory search capabilities
    show_memory_search_demo()

def show_memory_summary(data, name):
    """Show summary of memory data"""
    if name == "Main Memory State":
        context = data.get("context", {})
        print(f"   Current App: {context.get('active_app', 'Unknown')}")
        print(f"   Workflow Stage: {context.get('workflow_stage', 'Unknown')}")
        print(f"   User Intent: {context.get('user_intent', 'Unknown')}")
        print(f"   Memory Usage: {context.get('system_memory_percent', 0):.1f}%")
        
        short_term = data.get("short_term", [])
        long_term = data.get("long_term", [])
        print(f"   Short-term memories: {len(short_term)}")
        print(f"   Long-term memories: {len(long_term)}")
        
    elif name == "Conscious Memory":
        insights = data.get("insights", [])
        buffers = data.get("sensor_buffers", {})
        print(f"   Insights: {len(insights)} generated")
        print(f"   Sensor buffers: {len(buffers)} active")
        
        if insights:
            latest_insight = insights[-1]
            print(f"   Latest: {latest_insight.get('content', '')[:50]}...")
            
    elif name == "Conversation History":
        if isinstance(data, list):
            print(f"   Conversations: {len(data)} entries")
            if data:
                latest = data[-1]
                timestamp = latest.get("timestamp", "Unknown")
                print(f"   Latest: {timestamp}")
        
    elif name == "Last Context":
        if isinstance(data, dict):
            activity = data.get("user_activity", {})
            print(f"   Activity: {activity.get('current_activity', 'Unknown')}")
            print(f"   Context: {activity.get('productivity_context', 'Unknown')}")

def show_recent_ui_insights():
    """Show recent UI understanding insights"""
    print("\n🎯 RECENT UI UNDERSTANDING INSIGHTS:")
    print("="*60)
    
    # Check for recent UI analysis files
    ui_cache_dir = Path("cache/complete_ui_understanding")
    if ui_cache_dir.exists():
        ui_files = list(ui_cache_dir.glob("*.png"))
        json_files = list(ui_cache_dir.glob("*.json"))
        
        print(f"📸 Screenshots captured: {len(ui_files)}")
        print(f"📋 Analysis reports: {len(json_files)}")
        
        if ui_files:
            latest_screenshot = max(ui_files, key=lambda f: f.stat().st_mtime)
            modified = datetime.fromtimestamp(latest_screenshot.stat().st_mtime)
            print(f"   Latest screenshot: {latest_screenshot.name}")
            print(f"   Captured: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if json_files:
            for json_file in json_files[:3]:  # Show first 3
                try:
                    with open(json_file, 'r') as f:
                        analysis = json.load(f)
                        print(f"\n📊 Analysis: {json_file.name}")
                        if "ui_elements" in analysis:
                            total_elements = sum(len(subcat) for cat in analysis["ui_elements"].values() for subcat in cat.values())
                            print(f"   UI Elements: {total_elements} detected")
                        if "saas_platform" in analysis and analysis["saas_platform"]:
                            platform = analysis["saas_platform"]["platform"]
                            confidence = analysis["saas_platform"]["confidence"]
                            print(f"   SaaS Platform: {platform.title()} ({confidence:.0%})")
                        if "visualizations" in analysis:
                            viz_count = len(analysis["visualizations"])
                            print(f"   Visualizations: {viz_count} detected")
                except Exception as e:
                    print(f"   ⚠️ Error reading {json_file.name}: {e}")
    else:
        print("❌ No UI understanding cache found")
    
    # Show memory diagnostic logs
    print(f"\n📝 MEMORY DIAGNOSTIC LOGS:")
    print("="*40)
    
    log_files = [
        "logs/memory_system.log",
        "logs/memory/direct_integration.log",
        "logs/memory/memory_diagnostics.log"
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    print(f"📜 {log_file}: {len(lines)} log entries")
                    if lines:
                        # Show last few meaningful lines
                        meaningful_lines = [line for line in lines[-10:] if "INFO" in line or "WARNING" in line or "ERROR" in line]
                        for line in meaningful_lines[-3:]:
                            timestamp = line.split(' - ')[0] if ' - ' in line else ""
                            message = line.split(' - ')[-1].strip() if ' - ' in line else line.strip()
                            print(f"   {timestamp[-8:]}: {message[:60]}...")
            except Exception as e:
                print(f"   ⚠️ Error reading {log_file}: {e}")
        else:
            print(f"❌ {log_file}: Not found")

def show_memory_search_demo():
    """Show memory search capabilities"""
    print(f"\n🔍 MEMORY SEARCH & RETRIEVAL CAPABILITIES:")
    print("="*60)
    
    # Check if semantic search is available
    vector_db_path = Path("memory/vector_store.db")
    if vector_db_path.exists():
        size = vector_db_path.stat().st_size
        print(f"✅ Vector Database: {size:,} bytes")
        print("   Capabilities:")
        print("   • Semantic search across all memories")
        print("   • Context-aware retrieval")
        print("   • Professional activity matching")
        print("   • Workflow pattern recognition")
    else:
        print("❌ Vector database not found")
    
    # Show example search queries
    print(f"\n🎯 EXAMPLE SEARCH QUERIES YOU CAN RUN:")
    print("─" * 50)
    example_queries = [
        "debugging React applications",
        "Salesforce pipeline analysis", 
        "data visualization with charts",
        "UI design and prototyping",
        "system monitoring and DevOps"
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. '{query}'")
    
    print(f"\n💡 TO SEARCH MEMORY:")
    print("   Run: python -c \"from memory.enhanced_semantic_search import search_memory; search_memory('your_query')\"")

def show_live_memory_demo():
    """Show live memory demonstration"""
    print(f"\n🎬 LIVE MEMORY DEMONSTRATION:")
    print("="*60)
    
    try:
        # Try to import and show current memory state
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from memory.memory_system import MemorySystem
        
        print("🔄 Initializing memory system...")
        memory_system = MemorySystem()
        
        # Get current memory stats
        print(f"\n📊 CURRENT MEMORY STATUS:")
        print(f"   Short-term memory: {len(memory_system.short_term_memory)} entries")
        print(f"   Long-term memory: {len(memory_system.long_term_memory)} entries") 
        print(f"   Context memory: {len(memory_system.context_memory)} entries")
        
        # Show recent entries
        if memory_system.short_term_memory:
            print(f"\n🆕 RECENT SHORT-TERM MEMORIES:")
            for i, memory in enumerate(memory_system.short_term_memory[-3:], 1):
                timestamp = memory.get("timestamp", "Unknown")
                memory_type = memory.get("memory_type", "Unknown")
                print(f"   {i}. {memory_type} - {timestamp[-8:]}")
                
                # Show memory content preview
                if "ui_analysis" in memory:
                    ui_analysis = memory["ui_analysis"]
                    if "ui_elements" in ui_analysis:
                        elements = sum(len(subcat) for cat in ui_analysis["ui_elements"].values() for subcat in cat.values())
                        print(f"      UI Elements: {elements} detected")
                    if "saas_platform" in ui_analysis and ui_analysis["saas_platform"]:
                        platform = ui_analysis["saas_platform"]["platform"]
                        print(f"      Platform: {platform.title()}")
        
        print(f"\n✅ Live memory system is active and collecting insights!")
        
    except Exception as e:
        print(f"⚠️ Could not access live memory system: {e}")
        print("   Memory files are still available for manual inspection")

if __name__ == "__main__":
    view_all_memory_insights()
    show_live_memory_demo()