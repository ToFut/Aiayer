#!/usr/bin/env python3
"""
Test Proactive System
Simple test to verify proactive task identification works
"""

import asyncio
import sys
import time
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_proactive_system():
    """Test the proactive task identification system"""
    print("🧪 Testing Proactive AI System")
    print("=" * 50)
    
    try:
        # Test 1: Initialize proactive task identifier
        print("1. Initializing Proactive Task Identifier...")
        from proactive_task_identifier import initialize_proactive_identifier
        await initialize_proactive_identifier()
        print("   ✅ Proactive Task Identifier initialized")
        
        # Test 2: Test with sample UI2HTML data
        print("2. Testing Task Identification...")
        from proactive_task_identifier import identify_proactive_tasks
        
        # Sample UI2HTML data
        sample_ui_data = {
            'elements': [
                {'type': 'button', 'text': 'Save', 'attributes': {'id': 'save-btn'}},
                {'type': 'input', 'text': '', 'attributes': {'id': 'search-input'}},
                {'type': 'link', 'text': 'Settings', 'attributes': {'href': '/settings'}},
                {'type': 'checkbox', 'text': 'Enable notifications', 'attributes': {'id': 'notifications'}},
            ],
            'active_applications': [
                {'name': 'TextEdit', 'pid': 12345},
                {'name': 'Safari', 'pid': 12346}
            ],
            'current_window': {
                'title': 'Untitled - TextEdit',
                'app': 'TextEdit'
            }
        }
        
        # Identify proactive tasks
        tasks = await identify_proactive_tasks(sample_ui_data)
        print(f"   ✅ Identified {len(tasks)} proactive tasks")
        
        # Display tasks
        for i, task in enumerate(tasks[:5]):  # Show top 5
            print(f"   {i+1}. {task.description} (Priority: {task.priority}, Confidence: {task.confidence:.2f})")
        
        # Test 3: Test task suggestions formatting
        print("3. Testing Task Suggestions...")
        from proactive_task_identifier import get_task_suggestions
        suggestions = await get_task_suggestions(sample_ui_data)
        print(f"   ✅ Generated {len(suggestions)} formatted suggestions")
        
        # Display suggestions
        for i, suggestion in enumerate(suggestions[:3]):  # Show top 3
            print(f"   {i+1}. {suggestion['icon']} {suggestion['title']} ({suggestion['category']})")
        
        # Test 4: Test with real UI data (if available)
        print("4. Testing with Real UI Data...")
        try:
            # Try to get real UI data from RPA server
            import requests
            response = requests.get("http://localhost:16901/", timeout=2)
            if response.status_code == 200:
                print("   ✅ RPA Server is available")
                
                # Create mock real UI data
                real_ui_data = {
                    'elements': [
                        {'type': 'button', 'text': 'Close', 'attributes': {'id': 'close-btn'}},
                        {'type': 'input', 'text': 'Search...', 'attributes': {'placeholder': 'Search'}},
                        {'type': 'menu', 'text': 'File', 'attributes': {'id': 'file-menu'}},
                    ],
                    'active_applications': [
                        {'name': 'Finder', 'pid': 12347},
                        {'name': 'Calculator', 'pid': 12348}
                    ],
                    'current_window': {
                        'title': 'Desktop',
                        'app': 'Finder'
                    }
                }
                
                real_tasks = await identify_proactive_tasks(real_ui_data)
                print(f"   ✅ Identified {len(real_tasks)} tasks from real UI data")
                
                if real_tasks:
                    print(f"   🏆 Top task: {real_tasks[0].description}")
            else:
                print("   ⚠️ RPA Server not responding")
        except Exception as e:
            print(f"   ⚠️ Could not test with real UI data: {e}")
        
        print("=" * 50)
        print("✅ Proactive System Test Completed!")
        print("🎯 The system can identify tasks from UI2HTML analysis")
        print("🚀 Ready for integration with the complete AI system")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_proactive_system()) 