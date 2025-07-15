#!/usr/bin/env python3
"""
Test integration of UI2HTML system with existing codebase
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sensai_ui2html.integration import ScreenSensorReplacement, capture_screen
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor

def test_screen_sensor_replacement():
    """Test the screen sensor replacement."""
    print("=== Testing Screen Sensor Replacement ===\n")
    
    # Create replacement sensor
    sensor = ScreenSensorReplacement()
    
    # Test basic functionality
    print("1. Testing sensor start/stop...")
    assert sensor.start() == True
    assert sensor.is_active == True
    
    print("2. Testing screen capture...")
    screen_data = sensor.capture_screen({
        "test": True,
        "description": "Integration test"
    })
    
    print(f"   ✓ Captured screen data")
    print(f"   ✓ Sensor type: {screen_data['sensor_type']}")
    print(f"   ✓ Elements: {screen_data['element_count']}")
    print(f"   ✓ HTML length: {len(screen_data['html_content'])}")
    
    # Test memory query
    print("\n3. Testing memory query...")
    results = sensor.query_ui_memory("desktop", n_results=3)
    print(f"   ✓ Found {len(results)} results")
    
    # Test sensor info
    print("\n4. Testing sensor info...")
    info = sensor.get_sensor_info()
    print(f"   ✓ Sensor type: {info['sensor_type']}")
    print(f"   ✓ Active: {info['is_active']}")
    print(f"   ✓ Snapshots: {info['snapshot_count']}")
    
    # Stop sensor
    sensor.stop()
    assert sensor.is_active == False
    
    print("\n=== Screen sensor replacement test passed! ===")

def test_direct_integration():
    """Test direct integration functions."""
    print("\n=== Testing Direct Integration ===\n")
    
    # Test capture_screen function
    print("1. Testing capture_screen function...")
    screen_data = capture_screen({
        "direct_test": True
    })
    
    print(f"   ✓ Captured screen data")
    print(f"   ✓ Timestamp: {screen_data['timestamp']}")
    print(f"   ✓ Elements: {screen_data['element_count']}")
    
    print("\n=== Direct integration test passed! ===")

def test_ui2html_sensor():
    """Test the main UI2HTML sensor."""
    print("\n=== Testing UI2HTML Sensor ===\n")
    
    # Create sensor
    sensor = UI2HTMLSensor()
    
    # Test snapshot capture
    print("1. Testing snapshot capture...")
    sensor.start()
    snapshot = sensor.capture_snapshot({
        "sensor_test": True
    })
    
    print(f"   ✓ Snapshot ID: {snapshot['snapshot_id']}")
    print(f"   ✓ Elements: {snapshot['element_count']}")
    print(f"   ✓ HTML: {len(snapshot['html_content'])} chars")
    
    # Test memory query
    print("\n2. Testing memory query...")
    results = sensor.query_memory("macos", n_results=2)
    print(f"   ✓ Query results: {len(results)}")
    
    # Test recent snapshots
    print("\n3. Testing recent snapshots...")
    recent = sensor.list_recent_snapshots(limit=5)
    print(f"   ✓ Recent snapshots: {len(recent)}")
    
    sensor.stop()
    
    print("\n=== UI2HTML sensor test passed! ===")

def main():
    """Run all integration tests."""
    try:
        test_screen_sensor_replacement()
        test_direct_integration()
        test_ui2html_sensor()
        
        print("\n" + "="*60)
        print("🎉 All integration tests passed successfully!")
        print("The UI2HTML system is ready to replace screen sensors.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 