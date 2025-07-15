#!/usr/bin/env python3
"""
Demo script for SensAI.UI2HTMLMemory system
"""

import sys
import os
import time
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sensai_ui2html.ui2html_sensor import UI2HTMLSensor, capture_ui_snapshot, query_ui_memory

def demo_basic_usage():
    """Demonstrate basic usage of the UI2HTML sensor."""
    print("=== SensAI.UI2HTMLMemory Demo ===\n")
    
    # Create sensor
    print("1. Creating UI2HTML sensor...")
    sensor = UI2HTMLSensor()
    
    # Start sensor
    print("2. Starting sensor...")
    sensor.start()
    
    # Capture snapshot
    print("3. Capturing UI snapshot...")
    snapshot = sensor.capture_snapshot({
        "demo": True,
        "description": "Demo snapshot"
    })
    
    if snapshot:
        print(f"   ✓ Captured snapshot: {snapshot['snapshot_id']}")
        print(f"   ✓ Elements detected: {snapshot['element_count']}")
        print(f"   ✓ HTML generated: {len(snapshot['html_content'])} characters")
    else:
        print("   ✗ Failed to capture snapshot")
        return
    
    # Query memory
    print("\n4. Querying UI memory...")
    results = sensor.query_memory("button", n_results=3)
    print(f"   ✓ Found {len(results)} results for 'button' query")
    
    for i, result in enumerate(results, 1):
        print(f"   Result {i}: {result['id']} (distance: {result['distance']:.3f})")
    
    # Get sensor info
    print("\n5. Sensor information:")
    info = sensor.get_sensor_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Stop sensor
    print("\n6. Stopping sensor...")
    sensor.stop()
    
    print("\n=== Demo completed successfully! ===")

def demo_memory_query():
    """Demonstrate memory querying capabilities."""
    print("\n=== Memory Query Demo ===\n")
    
    # Query for different UI elements
    queries = ["button", "text", "input", "menu", "window"]
    
    for query in queries:
        print(f"Querying for '{query}'...")
        results = query_ui_memory(query, n_results=2)
        
        if results:
            print(f"  Found {len(results)} results:")
            for result in results:
                metadata = result['metadata']
                timestamp = metadata.get('timestamp', 'Unknown')
                element_count = metadata.get('element_count', 0)
                print(f"    - {result['id']} ({element_count} elements, {timestamp})")
        else:
            print("  No results found")
        print()

def demo_html_generation():
    """Demonstrate HTML generation from UI trees."""
    print("\n=== HTML Generation Demo ===\n")
    
    # Capture a snapshot
    snapshot = capture_ui_snapshot({"demo_html": True})
    
    if snapshot and snapshot.get('html_content'):
        html_content = snapshot['html_content']
        
        print("Generated HTML preview (first 500 chars):")
        print("-" * 50)
        print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        print("-" * 50)
        
        # Save to file
        with open("demo_ui.html", "w") as f:
            f.write(html_content)
        print("\nFull HTML saved to 'demo_ui.html'")
    else:
        print("Failed to generate HTML")

def main():
    """Run the complete demo."""
    try:
        demo_basic_usage()
        demo_memory_query()
        demo_html_generation()
        
        print("\n" + "="*50)
        print("All demos completed successfully!")
        print("Check 'demo_ui.html' for the generated HTML output.")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 