#!/usr/bin/env python3
"""
Test the improved universal screen detector
"""

from universal_screen_detector import UniversalScreenDetector
import time

def test_detection():
    """Test the improved detection system"""
    
    print("🔍 TESTING IMPROVED UNIVERSAL DETECTION")
    print("=" * 50)
    
    detector = UniversalScreenDetector()
    
    # Test search step
    step_description = "Search for 'segev halfon'"
    print(f"\n🎯 Testing step: {step_description}")
    
    coords = detector.get_coordinates_for_step(step_description)
    print(f"📍 Detected coordinates: {coords}")
    
    print("\n✅ Test complete")

if __name__ == "__main__":
    test_detection()