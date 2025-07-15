#!/usr/bin/env python3
"""
Complete SensAI.UI2HTMLMemory System Runner
"""

import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_components():
    """Test all system components."""
    print("🔧 Testing All System Components")
    print("=" * 50)
    
    tests = []
    
    # Test 1: UI Tree Extraction
    try:
        from ui_scraper.base_scraper import get_ui_tree
        ui_tree = get_ui_tree()
        tests.append(("UI Tree Extraction", True, f"Extracted {ui_tree.get('name', 'Unknown')} with {len(ui_tree.get('children', []))} children"))
    except Exception as e:
        tests.append(("UI Tree Extraction", False, str(e)))
    
    # Test 2: HTML Mapping
    try:
        from html_mapper import ui_node_to_html
        if tests[0][1]:  # Only if UI tree extraction worked
            html_content = ui_node_to_html(ui_tree)
            tests.append(("HTML Mapping", True, f"Generated {len(html_content)} characters of HTML"))
        else:
            tests.append(("HTML Mapping", False, "Skipped - UI tree extraction failed"))
    except Exception as e:
        tests.append(("HTML Mapping", False, str(e)))
    
    # Test 3: Memory Storage
    try:
        from memory_store import store_ui_snapshot, query_ui_by_text
        if tests[0][1]:  # Only if UI tree extraction worked
            snapshot_id = store_ui_snapshot(ui_tree, {"test": True})
            tests.append(("Memory Storage", True, f"Stored snapshot: {snapshot_id}"))
        else:
            tests.append(("Memory Storage", False, "Skipped - UI tree extraction failed"))
    except Exception as e:
        tests.append(("Memory Storage", False, str(e)))
    
    # Test 4: Memory Query
    try:
        if tests[2][1]:  # Only if memory storage worked
            results = query_ui_by_text("test", n_results=2)
            tests.append(("Memory Query", True, f"Found {len(results)} results"))
        else:
            tests.append(("Memory Query", False, "Skipped - Memory storage failed"))
    except Exception as e:
        tests.append(("Memory Query", False, str(e)))
    
    # Test 5: Sensor Class
    try:
        from ui2html_sensor import UI2HTMLSensor
        sensor = UI2HTMLSensor()
        sensor.start()
        snapshot = sensor.capture_snapshot({"sensor_test": True})
        sensor.stop()
        tests.append(("Sensor Class", True, f"Captured snapshot with {snapshot.get('element_count', 0)} elements"))
    except Exception as e:
        tests.append(("Sensor Class", False, str(e)))
    
    # Test 6: Integration Layer
    try:
        from integration import ScreenSensorReplacement
        sensor = ScreenSensorReplacement()
        sensor.start()
        data = sensor.capture_screen({"integration_test": True})
        sensor.stop()
        tests.append(("Integration Layer", True, f"Captured screen data with {data.get('element_count', 0)} elements"))
    except Exception as e:
        tests.append(("Integration Layer", False, str(e)))
    
    # Display results
    print("\n📊 Test Results:")
    print("-" * 50)
    
    passed = 0
    for test_name, success, message in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

def run_interactive_system():
    """Run the interactive system."""
    print("\n🚀 Starting Interactive SensAI.UI2HTMLMemory System")
    print("=" * 60)
    
    try:
        from ui2html_sensor import UI2HTMLSensor
        from integration import ScreenSensorReplacement
        
        while True:
            print("\n" + "="*50)
            print("🎯 SensAI.UI2HTMLMemory - Interactive Mode")
            print("="*50)
            print("1. Quick Capture - Capture one UI snapshot")
            print("2. Continuous Monitoring - Real-time capture")
            print("3. Memory Query - Search stored snapshots")
            print("4. Sensor Info - System status")
            print("5. Export Data - Save snapshots to file")
            print("6. Exit")
            print("="*50)
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                quick_capture()
            elif choice == '2':
                continuous_monitoring()
            elif choice == '3':
                memory_query()
            elif choice == '4':
                sensor_info()
            elif choice == '5':
                export_data()
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please select 1-6.")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

def quick_capture():
    """Quick capture mode."""
    print("\n📸 Quick Capture Mode")
    print("-" * 30)
    
    try:
        from integration import capture_screen
        
        snapshot = capture_screen({
            "mode": "quick_capture",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✅ Captured: {snapshot.get('snapshot_id', 'N/A')}")
        print(f"📊 Elements: {snapshot.get('element_count', 0)}")
        print(f"🌐 HTML: {len(snapshot.get('html_content', ''))} chars")
        print(f"⏰ Time: {snapshot.get('timestamp', 'N/A')}")
        
        # Show HTML preview
        html = snapshot.get('html_content', '')
        if html:
            print(f"\n📄 HTML Preview:")
            print("-" * 40)
            print(html[:200] + "..." if len(html) > 200 else html)
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def continuous_monitoring():
    """Continuous monitoring mode."""
    print("\n🔄 Continuous Monitoring Mode")
    print("-" * 35)
    print("Press Ctrl+C to stop")
    
    try:
        from ui2html_sensor import UI2HTMLSensor
        
        sensor = UI2HTMLSensor()
        sensor.start()
        
        count = 0
        start_time = time.time()
        
        while True:
            try:
                snapshot = sensor.capture_snapshot({
                    "mode": "continuous",
                    "count": count + 1
                })
                
                count += 1
                elapsed = time.time() - start_time
                
                print(f"📸 {count}: {snapshot.get('snapshot_id', 'N/A')} "
                      f"({snapshot.get('element_count', 0)} elements, {elapsed:.1f}s)")
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        sensor.stop()
        print(f"\n✅ Stopped. Captured {count} snapshots in {elapsed:.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def memory_query():
    """Memory query mode."""
    print("\n🔍 Memory Query Mode")
    print("-" * 25)
    
    try:
        from ui2html_sensor import UI2HTMLSensor
        
        sensor = UI2HTMLSensor()
        
        # Show recent snapshots
        recent = sensor.list_recent_snapshots(limit=5)
        print(f"📚 Recent snapshots: {len(recent)}")
        
        for i, snapshot in enumerate(recent, 1):
            metadata = snapshot.get('metadata', {})
            timestamp = metadata.get('timestamp', 'Unknown')
            element_count = metadata.get('element_count', 0)
            print(f"  {i}. {snapshot['id']} ({element_count} elements, {timestamp})")
        
        # Interactive query
        while True:
            query = input("\n🔍 Search term (or 'quit'): ").strip()
            if query.lower() == 'quit':
                break
            
            if query:
                results = sensor.query_memory(query, n_results=3)
                print(f"\n📋 Found {len(results)} results for '{query}':")
                
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    element_count = metadata.get('element_count', 0)
                    distance = result.get('distance', 0)
                    print(f"  {i}. {result['id']} (distance: {distance:.3f}, {element_count} elements)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def sensor_info():
    """Show sensor information."""
    print("\nℹ️  Sensor Information")
    print("-" * 25)
    
    try:
        from ui2html_sensor import UI2HTMLSensor
        
        sensor = UI2HTMLSensor()
        info = sensor.get_sensor_info()
        
        print(f"🔧 Type: {info.get('sensor_type', 'Unknown')}")
        print(f"🟢 Active: {info.get('is_active', False)}")
        print(f"📊 Snapshots: {info.get('snapshot_count', 0)}")
        print(f"🆔 Last: {info.get('last_snapshot_id', 'None')}")
        print(f"⚙️  Config: {info.get('config', {})}")
        
        # Check ChromaDB
        try:
            from memory_store import get_collection
            collection = get_collection()
            print(f"💾 ChromaDB: {'Connected' if collection else 'Not connected'}")
        except Exception as e:
            print(f"💾 ChromaDB: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def export_data():
    """Export snapshots to file."""
    print("\n💾 Export Data")
    print("-" * 15)
    
    try:
        from ui2html_sensor import UI2HTMLSensor
        
        sensor = UI2HTMLSensor()
        snapshots = sensor.list_recent_snapshots(limit=10)
        
        if snapshots:
            filename = f"ui_snapshots_{int(time.time())}.json"
            
            # Prepare data for export
            export_data = {
                "export_time": datetime.now().isoformat(),
                "snapshots": snapshots
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"✅ Exported {len(snapshots)} snapshots to {filename}")
        else:
            print("❌ No snapshots to export")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    print("🚀 SensAI.UI2HTMLMemory - Complete System")
    print("=" * 50)
    
    # Test all components first
    all_tests_passed = test_all_components()
    
    if all_tests_passed:
        print("\n🎉 All components working! Starting interactive system...")
        run_interactive_system()
    else:
        print("\n⚠️  Some components failed. Check the errors above.")
        print("💡 Try installing missing dependencies:")
        print("   pip install uiautomation chromadb openai")
        print("   pip install atomacos  # for better macOS support")

if __name__ == "__main__":
    main() 