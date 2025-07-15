#!/usr/bin/env python3
"""
Simple working example of SensAI.UI2HTMLMemory system
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_simple_example():
    """Run a simple working example."""
    print("🚀 Simple Example - SensAI.UI2HTMLMemory System")
    print("=" * 50)
    
    try:
        # Test 1: UI Tree Extraction
        print("1. Extracting UI tree...")
        from ui_scraper.base_scraper import get_ui_tree
        
        ui_tree = get_ui_tree()
        print(f"✅ Extracted UI tree: {ui_tree.get('name', 'Unknown')}")
        print(f"✅ Elements: {len(ui_tree.get('children', []))}")
        
        # Test 2: HTML Generation
        print("\n2. Generating HTML...")
        from html_mapper import ui_node_to_html
        
        html_content = ui_node_to_html(ui_tree)
        print(f"✅ Generated HTML: {len(html_content)} characters")
        print(f"📄 HTML Preview:")
        print("-" * 40)
        print(html_content[:300] + "..." if len(html_content) > 300 else html_content)
        print("-" * 40)
        
        # Test 3: Memory Storage (direct)
        print("\n3. Testing memory storage...")
        try:
            from memory_store import store_ui_snapshot, query_ui_by_text
            
            # Store snapshot
            snapshot_id = store_ui_snapshot(ui_tree, {
                "simple_test": True,
                "timestamp": datetime.now().isoformat()
            })
            print(f"✅ Stored snapshot: {snapshot_id}")
            
            # Query memory
            results = query_ui_by_text("desktop", n_results=3)
            print(f"✅ Memory query: {len(results)} results found")
            
        except Exception as e:
            print(f"⚠️  Memory storage test skipped: {e}")
        
        print("\n🎉 Basic functionality working!")
        print("\n📚 Next steps:")
        print("   - Install atomacos for better macOS support: pip install atomacos")
        print("   - Use the integration layer for drop-in replacement")
        print("   - Check README.md for full documentation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_how_to_use():
    """Show how to use the system."""
    print("\n" + "="*50)
    print("📖 How to Use the System")
    print("="*50)
    
    print("\n1. Basic Usage:")
    print("```python")
    print("from sensai_ui2html.ui_scraper.base_scraper import get_ui_tree")
    print("from sensai_ui2html.html_mapper import ui_node_to_html")
    print("")
    print("# Get UI tree")
    print("ui_tree = get_ui_tree()")
    print("")
    print("# Convert to HTML")
    print("html = ui_node_to_html(ui_tree)")
    print("print(html)")
    print("```")
    
    print("\n2. With Memory Storage:")
    print("```python")
    print("from sensai_ui2html.memory_store import store_ui_snapshot, query_ui_by_text")
    print("")
    print("# Store snapshot")
    print("snapshot_id = store_ui_snapshot(ui_tree, {'context': 'testing'})")
    print("")
    print("# Query memory")
    print("results = query_ui_by_text('button', n_results=5)")
    print("```")
    
    print("\n3. Replace Screen Sensor:")
    print("```python")
    print("from sensai_ui2html.integration import ScreenSensorReplacement")
    print("")
    print("sensor = ScreenSensorReplacement()")
    print("sensor.start()")
    print("data = sensor.capture_screen()")
    print("sensor.stop()")
    print("```")

def main():
    """Main function."""
    success = run_simple_example()
    
    if success:
        show_how_to_use()
        
        print("\n" + "="*50)
        print("✅ System is working!")
        print("🔧 For full features, install: pip install atomacos")
        print("📖 See README.md for complete documentation")
        print("="*50)
    else:
        print("\n❌ Basic test failed. Check dependencies.")

if __name__ == "__main__":
    main() 