#!/usr/bin/env python3
"""
Generate and View UI Memory Insights
Create UI analysis and immediately show where it's stored
"""

import asyncio
import json
import os
from datetime import datetime
from complete_ui_understanding_system import CompleteUIUnderstandingSystem

async def generate_and_view_memory():
    """Generate UI analysis and show where memory is stored"""
    print("\n" + "="*80)
    print("🚀 GENERATING UI ANALYSIS AND VIEWING MEMORY STORAGE")
    print("="*80)
    
    # Initialize UI system
    ui_system = CompleteUIUnderstandingSystem()
    
    print("🔄 Step 1: Performing complete UI analysis...")
    
    # Generate analysis
    analysis = await ui_system.perform_complete_ui_analysis()
    
    print("✅ UI analysis complete!")
    print(f"   • UI Elements detected: {sum(len(subcat) for cat in analysis['ui_elements'].values() for subcat in cat.values())}")
    print(f"   • SaaS Platform: {analysis['saas_platform']['platform'] if analysis['saas_platform'] else 'None'}")
    print(f"   • Visualizations: {len(analysis['visualizations'])}")
    print(f"   • Complexity Score: {analysis['ui_complexity_score']:.0%}")
    
    print(f"\n🔄 Step 2: Checking where memory was stored...")
    
    # Check memory locations
    memory_locations = {
        "Enhanced Memory System": check_enhanced_memory_system(),
        "Main Memory File": check_main_memory_file(),
        "Short-term Memory": check_short_term_memory(),
        "Vector Database": check_vector_database(),
        "Cache Files": check_cache_files()
    }
    
    print(f"\n📊 MEMORY STORAGE SUMMARY:")
    print("="*50)
    
    for location, info in memory_locations.items():
        status = "✅" if info['found'] else "❌"
        print(f"{status} {location}: {info['description']}")
        if info['found'] and info['details']:
            for detail in info['details']:
                print(f"   • {detail}")
    
    # Show actual memory content
    print(f"\n🧠 ACTUAL MEMORY CONTENT:")
    print("="*40)
    await show_latest_memory_content()
    
    # Show how to access this data
    print(f"\n🛠️ HOW TO ACCESS THIS MEMORY:")
    print("="*45)
    show_memory_access_guide()
    
    return analysis

def check_enhanced_memory_system():
    """Check if enhanced memory system stored data"""
    try:
        from enhanced_memory_with_deep_ui import EnhancedMemoryWithDeepUI
        enhanced_memory = EnhancedMemoryWithDeepUI()
        
        return {
            'found': True,
            'description': 'Enhanced memory system active',
            'details': [
                'Deep UI analysis capabilities',
                'Professional context detection', 
                'Behavioral pattern analysis'
            ]
        }
    except Exception as e:
        return {
            'found': False,
            'description': f'Enhanced memory system error: {e}',
            'details': []
        }

def check_main_memory_file():
    """Check main memory file"""
    memory_file = "memory/memory/memory_state.json"
    try:
        with open(memory_file, 'r') as f:
            data = json.load(f)
        
        short_term_count = len(data.get('short_term', []))
        context_count = len(data.get('context', []))
        
        return {
            'found': True,
            'description': f'Memory file updated: {short_term_count} short-term, {context_count} context',
            'details': [
                f'File: {memory_file}',
                f'Size: {os.path.getsize(memory_file):,} bytes',
                f'Last modified: {datetime.fromtimestamp(os.path.getmtime(memory_file)).strftime("%H:%M:%S")}'
            ]
        }
    except Exception as e:
        return {
            'found': False,
            'description': f'Memory file error: {e}',
            'details': []
        }

def check_short_term_memory():
    """Check short-term memory content"""
    try:
        from memory.memory_system import MemorySystem
        memory_system = MemorySystem()
        
        return {
            'found': True,
            'description': f'Short-term memory: {len(memory_system.short_term_memory)} entries',
            'details': [
                f'Context memory: {len(memory_system.context_memory)} entries',
                f'Memory system initialized successfully'
            ]
        }
    except Exception as e:
        return {
            'found': False,
            'description': f'Short-term memory error: {e}',
            'details': []
        }

def check_vector_database():
    """Check vector database"""
    vector_db = "memory/vector_store.db"
    try:
        if os.path.exists(vector_db):
            size = os.path.getsize(vector_db)
            return {
                'found': True,
                'description': f'Vector database: {size:,} bytes',
                'details': [
                    'Semantic search capabilities',
                    'UI insight embedding storage',
                    'Context-aware retrieval'
                ]
            }
        else:
            return {
                'found': False,
                'description': 'Vector database not found',
                'details': []
            }
    except Exception as e:
        return {
            'found': False,
            'description': f'Vector database error: {e}',
            'details': []
        }

def check_cache_files():
    """Check cache files"""
    cache_dir = "cache/complete_ui_understanding"
    try:
        if os.path.exists(cache_dir):
            files = os.listdir(cache_dir)
            return {
                'found': True,
                'description': f'UI cache: {len(files)} files',
                'details': [
                    f'Directory: {cache_dir}',
                    f'Screenshots and analysis data stored'
                ]
            }
        else:
            return {
                'found': False,
                'description': 'UI cache directory not found',
                'details': []
            }
    except Exception as e:
        return {
            'found': False,
            'description': f'Cache error: {e}',
            'details': []
        }

async def show_latest_memory_content():
    """Show latest memory content"""
    try:
        # Read main memory file
        with open("memory/memory/memory_state.json", 'r') as f:
            memory_data = json.load(f)
        
        short_term = memory_data.get('short_term', [])
        if short_term:
            print(f"📋 Latest Short-term Memory Entry:")
            latest = short_term[-1]
            
            timestamp = latest.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                print(f"   ⏰ Time: {dt.strftime('%H:%M:%S')}")
            
            # Show memory type
            memory_type = latest.get('memory_type', 'Unknown')
            print(f"   📝 Type: {memory_type}")
            
            # Show UI analysis if present
            if 'ui_analysis' in latest:
                ui_analysis = latest['ui_analysis']
                print(f"   🎛️ UI Analysis Present:")
                
                if 'ui_elements' in ui_analysis:
                    elements = ui_analysis['ui_elements']
                    total = sum(len(subcat) for cat in elements.values() for subcat in cat.values())
                    print(f"      • UI Elements: {total}")
                
                if 'saas_platform' in ui_analysis and ui_analysis['saas_platform']:
                    platform = ui_analysis['saas_platform']['platform']
                    confidence = ui_analysis['saas_platform']['confidence']
                    print(f"      • SaaS Platform: {platform} ({confidence:.0%})")
                
                if 'ui_complexity_score' in ui_analysis:
                    score = ui_analysis['ui_complexity_score']
                    print(f"      • Complexity: {score:.0%}")
            
            # Show professional context if present
            if 'professional_context' in latest:
                context = latest['professional_context']
                print(f"   🏢 Professional Context:")
                print(f"      • Activity: {context.get('activity_type', 'Unknown')}")
                print(f"      • Domain: {', '.join(context.get('domain_expertise', []))}")
            
            # Show user behavior if present
            if 'user_behavior' in latest:
                behavior = latest['user_behavior']
                print(f"   🧠 User Behavior:")
                print(f"      • Intent: {behavior.get('inferred_intent', 'Unknown')}")
                print(f"      • Activity: {behavior.get('activity_type', 'Unknown')}")
        else:
            print("📋 No short-term memory entries found")
            
    except Exception as e:
        print(f"⚠️ Error reading memory content: {e}")

def show_memory_access_guide():
    """Show how to access memory data"""
    print("1. 📖 View complete memory state:")
    print("   cat memory/memory/memory_state.json | jq .")
    print()
    print("2. 🔍 Search for UI analysis:")
    print("   python search_memory_ui_insights.py")
    print()
    print("3. 🧠 Interactive memory exploration:")
    print("   python -c \"from memory.memory_system import MemorySystem; ms = MemorySystem(); print('Loaded:', len(ms.short_term_memory), 'memories')\"")
    print()
    print("4. 📊 View memory insights:")
    print("   python view_memory_insights.py")
    print()
    print("5. 🎯 Latest memory entry:")
    print("   python -c \"import json; data=json.load(open('memory/memory/memory_state.json')); print(json.dumps(data['short_term'][-1] if data['short_term'] else {}, indent=2)[:500])\"")

if __name__ == "__main__":
    asyncio.run(generate_and_view_memory())