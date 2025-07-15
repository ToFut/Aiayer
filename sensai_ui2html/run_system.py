#!/usr/bin/env python3
"""
Simple script to run the SensAI.UI2HTMLMemory system
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui2html_sensor import UI2HTMLSensor
from integration import ScreenSensorReplacement, capture_screen

def show_menu():
    """Show the main menu."""
    print("\n" + "="*50)
    print("🎯 SensAI.UI2HTMLMemory System")
    print("="*50)
    print("1. Quick Capture - Capture one UI snapshot")
    print("2. Interactive Mode - Continuous monitoring")
    print("3. Memory Query - Search stored snapshots")
    print("4. Sensor Info - Show system status")
    print("5. Run Demo - Full system demonstration")
    print("6. Exit")
    print("="*50)

def quick_capture():
    """Capture a single UI snapshot."""
    print("\n📸 Quick Capture Mode")
    print("-" * 30)
    
    try:
        # Use the integration function for simple capture
        snapshot = capture_screen({
            "mode": "quick_capture",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✅ Captured snapshot: {snapshot.get('snapshot_id', 'N/A')}")
        print(f"📊 Elements detected: {snapshot.get('element_count', 0)}")
        print(f"🌐 HTML generated: {len(snapshot.get('html_content', ''))} characters")
        print(f"⏰ Timestamp: {snapshot.get('timestamp', 'N/A')}")
        
        # Show HTML preview
        html_content = snapshot.get('html_content', '')
        if html_content:
            print(f"\n📄 HTML Preview (first 200 chars):")
            print("-" * 40)
            print(html_content[:200] + "..." if len(html_content) > 200 else html_content)
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error capturing snapshot: {e}")

def interactive_mode():
    """Run interactive monitoring mode."""
    print("\n🔄 Interactive Monitoring Mode")
    print("-" * 35)
    print("Press Ctrl+C to stop monitoring")
    
    try:
        sensor = UI2HTMLSensor()
        sensor.start()
        
        snapshot_count = 0
        start_time = time.time()
        
        while True:
            try:
                snapshot = sensor.capture_snapshot({
                    "mode": "interactive",
                    "count": snapshot_count + 1
                })
                
                snapshot_count += 1
                elapsed = time.time() - start_time
                
                print(f"📸 Snapshot {snapshot_count}: {snapshot.get('snapshot_id', 'N/A')} "
                      f"({snapshot.get('element_count', 0)} elements, {elapsed:.1f}s elapsed)")
                
                time.sleep(2)  # Capture every 2 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        sensor.stop()
        print(f"\n✅ Monitoring stopped. Captured {snapshot_count} snapshots in {elapsed:.1f} seconds.")
        
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")

def memory_query():
    """Query stored snapshots."""
    print("\n🔍 Memory Query Mode")
    print("-" * 25)
    
    try:
        sensor = UI2HTMLSensor()
        
        # Get recent snapshots
        recent = sensor.list_recent_snapshots(limit=5)
        print(f"📚 Found {len(recent)} recent snapshots:")
        
        for i, snapshot in enumerate(recent, 1):
            metadata = snapshot.get('metadata', {})
            timestamp = metadata.get('timestamp', 'Unknown')
            element_count = metadata.get('element_count', 0)
            print(f"  {i}. {snapshot['id']} ({element_count} elements, {timestamp})")
        
        # Interactive query
        while True:
            query = input("\n🔍 Enter search term (or 'quit' to exit): ").strip()
            if query.lower() == 'quit':
                break
            
            if query:
                results = sensor.query_memory(query, n_results=3)
                print(f"\n📋 Found {len(results)} results for '{query}':")
                
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    timestamp = metadata.get('timestamp', 'Unknown')
                    element_count = metadata.get('element_count', 0)
                    distance = result.get('distance', 0)
                    print(f"  {i}. {result['id']} (distance: {distance:.3f}, {element_count} elements)")
        
    except Exception as e:
        print(f"❌ Error in memory query: {e}")

def sensor_info():
    """Show sensor information."""
    print("\nℹ️  Sensor Information")
    print("-" * 25)
    
    try:
        sensor = UI2HTMLSensor()
        info = sensor.get_sensor_info()
        
        print(f"🔧 Sensor Type: {info.get('sensor_type', 'Unknown')}")
        print(f"🟢 Active: {info.get('is_active', False)}")
        print(f"📊 Snapshots Captured: {info.get('snapshot_count', 0)}")
        print(f"🆔 Last Snapshot: {info.get('last_snapshot_id', 'None')}")
        print(f"⚙️  Config: {info.get('config', {})}")
        
        # Show ChromaDB status
        try:
            from memory_store import get_collection
            collection = get_collection()
            if collection:
                print(f"💾 ChromaDB: Connected")
            else:
                print(f"💾 ChromaDB: Not connected")
        except Exception as e:
            print(f"💾 ChromaDB: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error getting sensor info: {e}")

def run_demo():
    """Run the full demo."""
    print("\n🎬 Running Full Demo")
    print("-" * 20)
    
    try:
        from examples.demo import main as demo_main
        demo_main()
    except Exception as e:
        print(f"❌ Error running demo: {e}")

def main():
    """Main function."""
    print("🚀 Starting SensAI.UI2HTMLMemory System...")
    
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect an option (1-6): ").strip()
            
            if choice == '1':
                quick_capture()
            elif choice == '2':
                interactive_mode()
            elif choice == '3':
                memory_query()
            elif choice == '4':
                sensor_info()
            elif choice == '5':
                run_demo()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 