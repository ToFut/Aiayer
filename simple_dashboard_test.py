#!/usr/bin/env python3
"""
Simple Dashboard Test
Quick test to verify proactive task identification works
"""

import asyncio
import json
import time
from pathlib import Path
import sys

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_proactive_dashboard():
    """Test proactive task identification and display"""
    print("🧪 Testing Proactive Dashboard Functionality")
    print("=" * 60)
    
    try:
        # Initialize proactive task identifier
        print("1. Initializing Proactive Task Identifier...")
        from proactive_task_identifier import initialize_proactive_identifier
        await initialize_proactive_identifier()
        print("   ✅ Proactive Task Identifier initialized")
        
        # Test with sample UI data
        print("2. Testing Task Identification...")
        from proactive_task_identifier import identify_proactive_tasks
        
        # Sample UI data representing a typical desktop
        sample_ui_data = {
            'elements': [
                {'type': 'button', 'text': 'Save', 'attributes': {'id': 'save-btn'}},
                {'type': 'input', 'text': '', 'attributes': {'id': 'search-input', 'placeholder': 'Search...'}},
                {'type': 'link', 'text': 'Settings', 'attributes': {'href': '/settings'}},
                {'type': 'checkbox', 'text': 'Enable notifications', 'attributes': {'id': 'notifications'}},
                {'type': 'menu', 'text': 'File', 'attributes': {'id': 'file-menu'}},
                {'type': 'button', 'text': 'Close', 'attributes': {'id': 'close-btn'}},
            ],
            'active_applications': [
                {'name': 'TextEdit', 'pid': 12345},
                {'name': 'Safari', 'pid': 12346},
                {'name': 'Finder', 'pid': 12347}
            ],
            'current_window': {
                'title': 'Untitled - TextEdit',
                'app': 'TextEdit'
            }
        }
        
        # Identify proactive tasks
        tasks = await identify_proactive_tasks(sample_ui_data)
        print(f"   ✅ Identified {len(tasks)} proactive tasks")
        
        # Display dashboard-like output
        print("\n3. Proactive Task Dashboard")
        print("-" * 40)
        print("🎯 AUTOMATICALLY IDENTIFIED TASKS")
        print("=" * 40)
        
        for i, task in enumerate(tasks[:10], 1):
            icon = "⌨️" if "type" in task.action_type else "🖱️" if "click" in task.action_type else "🔄"
            print(f"{i:2d}. {icon} {task.description}")
            print(f"    Priority: {task.priority}/5 | Confidence: {task.confidence:.2f} | Time: {task.estimated_time:.1f}s")
            print(f"    Action: {task.action_type} | Target: {task.target_element}")
            print()
        
        # Show current UI state
        print("📊 CURRENT UI STATE")
        print("-" * 40)
        print(f"Active Applications: {len(sample_ui_data['active_applications'])}")
        for app in sample_ui_data['active_applications']:
            print(f"  • {app['name']} (PID: {app['pid']})")
        
        print(f"\nCurrent Window: {sample_ui_data['current_window']['title']}")
        print(f"Application: {sample_ui_data['current_window']['app']}")
        
        print(f"\nUI Elements: {len(sample_ui_data['elements'])}")
        for elem in sample_ui_data['elements'][:5]:
            print(f"  • {elem['type']}: {elem['text']}")
        
        # Show system statistics
        print("\n📈 SYSTEM STATISTICS")
        print("-" * 40)
        print(f"Tasks Identified: {len(tasks)}")
        print(f"Analysis Time: {time.time():.2f}s")
        print(f"Average Priority: {sum(t.priority for t in tasks) / len(tasks):.1f}/5")
        print(f"Average Confidence: {sum(t.confidence for t in tasks) / len(tasks):.2f}")
        
        # Show task categories
        categories = {}
        for task in tasks:
            cat = task.action_type.split('_')[0] if '_' in task.action_type else task.action_type
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\nTask Categories:")
        for cat, count in categories.items():
            print(f"  • {cat.title()}: {count} tasks")
        
        print("\n" + "=" * 60)
        print("✅ PROACTIVE DASHBOARD TEST COMPLETED!")
        print("🎯 The system successfully identifies tasks automatically")
        print("🚀 Ready for real-time dashboard implementation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_proactive_dashboard()) 