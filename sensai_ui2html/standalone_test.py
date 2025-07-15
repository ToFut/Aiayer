#!/usr/bin/env python3
"""
Standalone test script for SensAI.UI2HTMLMemory system
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ui2html_system():
    """Test the UI2HTML system directly."""
    print("🚀 Standalone Test - SensAI.UI2HTMLMemory System")
    print("=" * 55)
    
    try:
        # Test UI tree extraction
        print("1. Testing UI tree extraction...")
        from ui_scraper.base_scraper import get_ui_tree
        
        ui_tree = get_ui_tree()
        print(f"✅ UI tree extracted: {ui_tree.get('name', 'Unknown')}")
        print(f"✅ Children count: {len(ui_tree.get('children', []))}")
        
        # Test HTML mapping
        print("\n2. Testing HTML mapping...")
        from html_mapper import ui_node_to_html
        
        html_content = ui_node_to_html(ui_tree)
        print(f"✅ HTML generated: {len(html_content)} characters")
        print(f"📄 Preview: {html_content[:100]}...")
        
        # Test memory storage
        print("\n3. Testing memory storage...")
        from memory_store import store_ui_snapshot, query_ui_by_text
        
        snapshot_id = store_ui_snapshot(ui_tree, {"test": True})
        print(f"✅ Snapshot stored: {snapshot_id}")
        
        # Test memory query
        results = query_ui_by_text("test", n_results=2)
        print(f"✅ Memory query successful: {len(results)} results")
        
        # Test sensor class
        print("\n4. Testing sensor class...")
        from ui2html_sensor import UI2HTMLSensor
        
        sensor = UI2HTMLSensor()
        sensor.start()
        
        snapshot = sensor.capture_snapshot({"standalone_test": True})
        print(f"✅ Sensor capture: {snapshot.get('snapshot_id', 'N/A')}")
        print(f"✅ Elements: {snapshot.get('element_count', 0)}")
        
        sensor.stop()
        
        print("\n🎉 All tests passed! System is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """Show usage examples."""
    print("\n📚 Usage Examples:")
    print("-" * 20)
    
    examples = [
        {
            "title": "Basic Capture",
            "code": """from sensai_ui2html.integration import capture_screen
snapshot = capture_screen({"context": "testing"})
print(f"Elements: {snapshot['element_count']}")"""
        },
        {
            "title": "Sensor Usage",
            "code": """from sensai_ui2html.ui2html_sensor import UI2HTMLSensor
sensor = UI2HTMLSensor()
sensor.start()
snapshot = sensor.capture_snapshot()
sensor.stop()"""
        },
        {
            "title": "Memory Query",
            "code": """from sensai_ui2html.ui2html_sensor import query_ui_memory
results = query_ui_memory("button", n_results=5)
for result in results:
    print(f"Found: {result['id']}")"""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print("```python")
        print(example['code'])
        print("```")

def main():
    """Main function."""
    success = test_ui2html_system()
    
    if success:
        show_usage_examples()
        
        print("\n" + "="*55)
        print("✅ System is ready to use!")
        print("📖 Check README.md for full documentation")
        print("🔧 Run 'python examples/demo.py' for full demo")
        print("="*55)
    else:
        print("\n❌ System test failed. Check dependencies and permissions.")

if __name__ == "__main__":
    main() 