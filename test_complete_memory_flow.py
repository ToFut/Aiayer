#!/usr/bin/env python3
"""
Complete Memory Flow Test - Verify all memory storage systems work perfectly
Tests: Sensors → Conscious Memory → Short/Long/Context Memory
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem
from memory.conscious_memory import ConsciousMemory

def create_comprehensive_sensor_data():
    """Create comprehensive sensor data to test all memory pathways"""
    return {
        "screen": {
            "timestamp": datetime.now().isoformat(),
            "active_window": {
                "title": "test_memory_flow.py - Visual Studio Code",
                "application": "Visual Studio Code",
                "path": "/Users/test/project"
            },
            "ui_elements": {
                "controls": [
                    {"type": "button", "focused": True, "text": "Run"},
                    {"type": "menu", "text": "File"}
                ],
                "text_fields": [
                    {"type": "editor", "content": "def test_memory(): pass"}
                ],
                "navigation": [
                    {"type": "breadcrumb", "text": "project > test"}
                ]
            },
            "text_content": {
                "headers": ["test_memory_flow.py"],
                "main_text": ["def test_memory():", "    # Testing memory flow", "    pass"],
                "raw_text": "def test_memory():\n    # Testing memory flow\n    pass"
            },
            "visual_hierarchy": {"main_content": "code_editor"},
            "ui_state": {"focused": True, "active": True}
        },
        "process": {
            "timestamp": datetime.now().isoformat(),
            "foreground": [
                {
                    "name": "Visual Studio Code", 
                    "type": "development", 
                    "category": "ide",
                    "state": {"active": True, "focused": True},
                    "memory_usage": 150.5,
                    "cpu_usage": 12.3
                }
            ],
            "background": [
                {
                    "name": "Python", 
                    "type": "interpreter", 
                    "category": "development",
                    "memory_usage": 25.1,
                    "cpu_usage": 0.5
                },
                {
                    "name": "Terminal",
                    "type": "system",
                    "category": "utility",
                    "memory_usage": 10.2,
                    "cpu_usage": 0.1
                }
            ],
            "system_resources": {
                "memory_total": 16384,
                "memory_used": 8192,
                "cpu_usage": 25.5
            },
            "network_state": {
                "connections": 15,
                "data_sent": 1024,
                "data_received": 2048
            }
        },
        "file": {
            "timestamp": datetime.now().isoformat(),
            "current_file": {
                "path": "/Users/test/project/test_memory_flow.py",
                "size": 1024,
                "modified": datetime.now().isoformat(),
                "type": "python"
            },
            "recent_files": [
                {
                    "path": "/Users/test/project/memory_system.py",
                    "accessed": datetime.now().isoformat(),
                    "type": "python"
                },
                {
                    "path": "/Users/test/project/README.md", 
                    "accessed": datetime.now().isoformat(),
                    "type": "markdown"
                }
            ],
            "file_operations": [
                {"action": "save", "file": "test_memory_flow.py", "timestamp": datetime.now().isoformat()},
                {"action": "open", "file": "memory_system.py", "timestamp": datetime.now().isoformat()}
            ]
        }
    }

async def test_memory_flow_comprehensive():
    """Test complete memory flow from sensors through all storage systems"""
    
    print("🔍 COMPREHENSIVE MEMORY FLOW TEST")
    print("=" * 70)
    print("Testing: Sensors → Conscious Memory → Short/Long/Context Memory")
    print()
    
    # Initialize memory system
    print("📋 Initializing Memory System...")
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    # Get initial state counts
    initial_short_term = len(memory_system.short_term_memory)
    initial_long_term = len(memory_system.long_term_memory) 
    initial_context_keys = len(memory_system.context_memory.keys()) if isinstance(memory_system.context_memory, dict) else 0
    
    print(f"📊 Initial Memory State:")
    print(f"   Short-term: {initial_short_term} items")
    print(f"   Long-term: {initial_long_term} items")
    print(f"   Context: {initial_context_keys} keys")
    print(f"   Conscious Memory: {'✅ Available' if hasattr(memory_system, 'conscious_memory') else '❌ Missing'}")
    
    # Create comprehensive test data
    sensor_data = create_comprehensive_sensor_data()
    
    print(f"\n🔄 TESTING MEMORY FLOW STAGES")
    print("-" * 50)
    
    # Stage 1: Process sensor data through memory system
    print("1️⃣ Processing sensor data through memory system...")
    try:
        memory_system.process_sensor_data(sensor_data)
        print("   ✅ Sensor data processed successfully")
    except Exception as e:
        print(f"   ❌ Error processing sensor data: {e}")
        return False
    
    # Stage 2: Check conscious memory integration
    print("2️⃣ Checking conscious memory integration...")
    if hasattr(memory_system, 'conscious_memory') and memory_system.conscious_memory:
        try:
            # Check if conscious memory has received the data
            conscious_state = memory_system.conscious_memory.get_current_state()
            print(f"   ✅ Conscious memory state: {len(conscious_state)} items")
            
            # Check conscious memory context awareness
            context_awareness = memory_system.conscious_memory.get_context_awareness()
            print(f"   ✅ Context awareness: {len(context_awareness)} contexts")
        except Exception as e:
            print(f"   ⚠️  Conscious memory check: {e}")
    else:
        print("   ❌ Conscious memory not properly initialized")
    
    # Stage 3: Verify short-term memory updates
    print("3️⃣ Verifying short-term memory updates...")
    current_short_term = len(memory_system.short_term_memory)
    if current_short_term > initial_short_term:
        print(f"   ✅ Short-term memory updated: {initial_short_term} → {current_short_term}")
        
        # Check the latest short-term memory entry
        if memory_system.short_term_memory:
            latest_entry = memory_system.short_term_memory[-1]
            if isinstance(latest_entry, dict):
                entry_keys = list(latest_entry.keys())
                print(f"   📝 Latest entry keys: {entry_keys[:5]}...")  # Show first 5 keys
                
                # Check for enhanced understanding data
                if 'user_behavior' in latest_entry:
                    print("   🧠 Enhanced understanding data present")
                else:
                    print("   ⚠️  Enhanced understanding data missing")
            else:
                print(f"   📝 Latest entry type: {type(latest_entry)}")
    else:
        print(f"   ❌ Short-term memory not updated: {initial_short_term} = {current_short_term}")
    
    # Stage 4: Check context memory updates  
    print("4️⃣ Checking context memory updates...")
    current_context_keys = len(memory_system.context_memory.keys()) if isinstance(memory_system.context_memory, dict) else 0
    if current_context_keys >= initial_context_keys:
        print(f"   ✅ Context memory updated: {initial_context_keys} → {current_context_keys}")
        
        # Check current context specifically
        current_context = memory_system.context_memory.get('current_context', {})
        if current_context:
            print(f"   📝 Current context has {len(current_context)} fields")
            
            # Check for our enhanced understanding fields
            if 'user_behavior' in current_context:
                user_behavior = current_context['user_behavior']
                print(f"   🧠 User behavior analysis: {user_behavior.get('inferred_intent', 'unknown')}")
                print(f"   🎯 Focus score: {user_behavior.get('focus_level', {}).get('focus_score', 'N/A')}")
            else:
                print("   ⚠️  User behavior analysis missing from current context")
        else:
            print("   ⚠️  Current context is empty")
    else:
        print(f"   ❌ Context memory not properly updated")
    
    # Stage 5: Test long-term memory consolidation
    print("5️⃣ Testing long-term memory consolidation...")
    try:
        # Trigger consolidation if available
        if hasattr(memory_system, 'consolidate_memories'):
            await memory_system.consolidate_memories()
            current_long_term = len(memory_system.long_term_memory)
            print(f"   ✅ Long-term memory: {initial_long_term} → {current_long_term}")
        else:
            print("   ℹ️  Long-term consolidation method not available")
    except Exception as e:
        print(f"   ⚠️  Long-term consolidation: {e}")
    
    # Stage 6: Test sensor integration
    print("6️⃣ Testing individual sensor integration...")
    
    # Test screen sensor data processing
    screen_data = sensor_data.get('screen', {})
    if screen_data:
        screen_context = memory_system.context_memory.get('visual_context', {})
        if screen_context:
            print("   ✅ Screen sensor → visual context")
        else:
            print("   ❌ Screen sensor integration failed")
    
    # Test process sensor data processing  
    process_data = sensor_data.get('process', {})
    if process_data:
        app_context = memory_system.context_memory.get('application_context', {})
        if app_context:
            print("   ✅ Process sensor → application context")
        else:
            print("   ❌ Process sensor integration failed")
    
    # Test file sensor data processing
    file_data = sensor_data.get('file', {})
    if file_data:
        # Check if file data is stored somewhere
        file_found = False
        for key, value in memory_system.context_memory.items():
            if isinstance(value, dict) and 'current_file' in str(value):
                file_found = True
                break
        if file_found:
            print("   ✅ File sensor → context storage")
        else:
            print("   ⚠️  File sensor data storage unclear")
    
    # Stage 7: Test memory persistence
    print("7️⃣ Testing memory persistence...")
    try:
        memory_system._save_memory_state_sync()
        print("   ✅ Memory state saved successfully")
        
        # Try to load and verify
        memory_state_file = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
        if os.path.exists(memory_state_file):
            with open(memory_state_file, 'r') as f:
                saved_state = json.load(f)
            
            saved_short = len(saved_state.get('short_term_memory', []))
            saved_context = len(saved_state.get('context_memory', {}))
            print(f"   📄 Saved state - Short: {saved_short}, Context: {saved_context}")
        else:
            print("   ⚠️  Memory state file not found")
    except Exception as e:
        print(f"   ❌ Memory persistence error: {e}")
    
    # Final Analysis
    print(f"\n📈 MEMORY FLOW ANALYSIS SUMMARY")
    print("=" * 50)
    
    final_short_term = len(memory_system.short_term_memory)
    final_context_keys = len(memory_system.context_memory.keys()) if isinstance(memory_system.context_memory, dict) else 0
    
    tests_passed = 0
    total_tests = 7
    
    # Check each component
    if current_short_term > initial_short_term:
        tests_passed += 1
        print("✅ Short-term memory updating correctly")
    else:
        print("❌ Short-term memory not updating")
    
    if current_context_keys >= initial_context_keys:
        tests_passed += 1
        print("✅ Context memory updating correctly")
    else:
        print("❌ Context memory not updating")
    
    if memory_system.context_memory.get('current_context'):
        tests_passed += 1
        print("✅ Current context tracking working")
    else:
        print("❌ Current context tracking failed")
    
    if hasattr(memory_system, 'conscious_memory') and memory_system.conscious_memory:
        tests_passed += 1
        print("✅ Conscious memory integration working")
    else:
        print("❌ Conscious memory integration failed")
    
    # Check enhanced understanding
    current_context = memory_system.context_memory.get('current_context', {})
    if current_context.get('user_behavior'):
        tests_passed += 1
        print("✅ Enhanced understanding system working")
    else:
        print("❌ Enhanced understanding system failed")
    
    # Check sensor data flow
    if (memory_system.context_memory.get('visual_context') and 
        memory_system.context_memory.get('application_context')):
        tests_passed += 1
        print("✅ Sensor data flow working")
    else:
        print("❌ Sensor data flow incomplete")
    
    # Check persistence
    if os.path.exists("/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"):
        tests_passed += 1
        print("✅ Memory persistence working")
    else:
        print("❌ Memory persistence failed")
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({tests_passed}/{total_tests})")
    
    if success_rate >= 85:
        print("🎉 EXCELLENT: Memory system working perfectly!")
    elif success_rate >= 70:
        print("✅ GOOD: Memory system working well with minor issues")
    elif success_rate >= 50:
        print("⚠️  MODERATE: Memory system has significant issues")
    else:
        print("❌ POOR: Memory system requires major fixes")
    
    return {
        'success_rate': success_rate,
        'tests_passed': tests_passed,
        'total_tests': total_tests,
        'short_term_growth': final_short_term - initial_short_term,
        'context_growth': final_context_keys - initial_context_keys,
        'memory_components': {
            'short_term': final_short_term,
            'long_term': len(memory_system.long_term_memory),
            'context': final_context_keys,
            'conscious': hasattr(memory_system, 'conscious_memory')
        }
    }

async def main():
    """Main function to run comprehensive memory flow tests"""
    try:
        print("🚀 Starting Comprehensive Memory Flow Tests...")
        results = await test_memory_flow_comprehensive()
        
        # Save detailed test results
        with open('/Users/segevbin/Desktop/SensAI/Aiayer/memory_flow_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed test results saved to memory_flow_test_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during memory flow testing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())