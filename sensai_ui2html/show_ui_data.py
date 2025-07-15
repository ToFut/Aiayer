#!/usr/bin/env python3
"""
Show actual UI information found in stored snapshots
"""

from memory_store import list_snapshots, get_ui_memory
import json

def show_ui_data():
    """Display actual UI information from stored snapshots."""
    print("🔍 ACTUAL UI INFORMATION FOUND")
    print("=" * 50)
    
    # Get recent snapshots
    snapshots = list_snapshots(3)
    
    if not snapshots:
        print("❌ No snapshots found")
        return
    
    print(f"📊 Found {len(snapshots)} recent snapshots")
    print()
    
    # Show latest snapshot details
    latest = snapshots[0]
    print("📸 LATEST SNAPSHOT:")
    print(f"   ID: {latest['id']}")
    print(f"   Timestamp: {latest['metadata']['timestamp']}")
    print(f"   Elements: {latest['metadata']['element_count']}")
    print()
    
    # Get detailed data
    detailed = get_ui_memory(latest['id'])
    if detailed:
        print("📄 HTML CONTENT PREVIEW:")
        print("-" * 30)
        html_content = detailed['metadata']['html_content']
        print(html_content[:800] + "..." if len(html_content) > 800 else html_content)
        print()
        
        # Show UI tree structure
        print("🌳 UI TREE STRUCTURE:")
        print("-" * 30)
        ui_tree = json.loads(detailed['metadata']['ui_tree'])
        print(f"Root: {ui_tree.get('name', 'Unknown')} ({ui_tree.get('type', 'Unknown')})")
        print(f"Children: {len(ui_tree.get('children', []))}")
        
        # Show first few children
        for i, child in enumerate(ui_tree.get('children', [])[:5]):
            print(f"  {i+1}. {child.get('name', 'Unknown')} ({child.get('type', 'Unknown')})")
            if child.get('children'):
                print(f"     └─ {len(child['children'])} sub-elements")
        
        if len(ui_tree.get('children', [])) > 5:
            print(f"  ... and {len(ui_tree.get('children', [])) - 5} more elements")
    
    print()
    print("💡 This shows REAL macOS UI data extracted from your actual applications!")

if __name__ == "__main__":
    show_ui_data() 