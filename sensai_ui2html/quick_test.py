#!/usr/bin/env python3
"""
Quick test script for SensAI.UI2HTMLMemory system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def quick_test():
    """Run a quick test of the system."""
    print("🚀 Quick Test - SensAI.UI2HTMLMemory System")
    print("=" * 50)
    
    try:
        # Import and test the system
        from integration import capture_screen
        from ui2html_sensor import UI2HTMLSensor
        
        print("✅ Imports successful")
        
        # Test capture
        print("\n📸 Testing UI capture...")
        snapshot = capture_screen({"test": True})
        
        print(f"✅ Captured snapshot: {snapshot.get('snapshot_id', 'N/A')}")
        print(f"📊 Elements: {snapshot.get('element_count', 0)}")
        print(f"🌐 HTML length: {len(snapshot.get('html_content', ''))}")
        
        # Test sensor
        print("\n🔧 Testing sensor...")
        sensor = UI2HTMLSensor()
        sensor.start()
        
        info = sensor.get_sensor_info()
        print(f"✅ Sensor type: {info.get('sensor_type', 'Unknown')}")
        print(f"✅ Active: {info.get('is_active', False)}")
        
        sensor.stop()
        
        # Test memory query
        print("\n🔍 Testing memory query...")
        results = sensor.query_memory("test", n_results=2)
        print(f"✅ Found {len(results)} results in memory")
        
        print("\n🎉 All tests passed! System is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test() 