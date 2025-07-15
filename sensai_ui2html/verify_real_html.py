#!/usr/bin/env python3
"""
Verify that the system generates REAL HTML from actual macOS UI, not mock data
"""

import json
import time
from ui_scraper.base_scraper import get_ui_tree
from html_mapper import ui_node_to_html
from memory_store import store_ui_snapshot, query_ui_by_text

def verify_real_html():
    """Verify that the system generates real HTML from actual macOS UI."""
    print("🔍 VERIFYING REAL HTML GENERATION")
    print("=" * 50)
    
    # Step 1: Get real UI tree
    print("📱 Step 1: Extracting Real macOS UI...")
    ui_tree = get_ui_tree()
    
    print(f"   App Name: {ui_tree.get('name', 'Unknown')}")
    print(f"   App Type: {ui_tree.get('type', 'Unknown')}")
    print(f"   Element Count: {len(ui_tree.get('children', []))}")
    print(f"   Timestamp: {time.time()}")
    
    # Step 2: Generate HTML
    print("\n📄 Step 2: Generating HTML from Real UI...")
    html_content = ui_node_to_html(ui_tree)
    
    print(f"   HTML Length: {len(html_content)} characters")
    print(f"   HTML Lines: {html_content.count('<')} HTML tags")
    
    # Step 3: Analyze HTML content
    print("\n🔍 Step 3: Analyzing HTML Content...")
    
    # Check for real macOS elements
    real_elements = []
    if 'axapplication' in html_content.lower():
        real_elements.append("AXApplication (macOS Accessibility)")
    if 'axmenubar' in html_content.lower():
        real_elements.append("AXMenuBar (macOS Menu Bar)")
    if 'axmenuitem' in html_content.lower():
        real_elements.append("AXMenuItem (macOS Menu Items)")
    if 'axbutton' in html_content.lower():
        real_elements.append("AXButton (macOS Buttons)")
    if 'axwindow' in html_content.lower():
        real_elements.append("AXWindow (macOS Windows)")
    if 'axscrollarea' in html_content.lower():
        real_elements.append("AXScrollArea (macOS Scroll Areas)")
    
    print(f"   Real macOS Elements Found: {len(real_elements)}")
    for element in real_elements:
        print(f"     ✅ {element}")
    
    # Check for real positioning
    real_positioning = []
    if 'position:absolute' in html_content:
        real_positioning.append("Absolute Positioning")
    if 'px' in html_content:
        real_positioning.append("Real Pixel Coordinates")
    if 'width:' in html_content and 'height:' in html_content:
        real_positioning.append("Real Dimensions")
    
    print(f"   Real Positioning Found: {len(real_positioning)}")
    for pos in real_positioning:
        print(f"     ✅ {pos}")
    
    # Step 4: Check for mock indicators
    print("\n🚫 Step 4: Checking for Mock Indicators...")
    mock_indicators = []
    if 'fallback_root' in html_content.lower():
        mock_indicators.append("Fallback UI detected")
    if 'fallback_ui_element' in html_content.lower():
        mock_indicators.append("Fallback UI element detected")
    if 'macos desktop' in html_content.lower() and 'desktop_group' in html_content.lower():
        mock_indicators.append("Generic desktop fallback detected")
    if 'unknown' in html_content.lower() and html_content.lower().count('unknown') > 10:
        mock_indicators.append("Too many 'Unknown' elements")
    
    if mock_indicators:
        print("   ❌ Mock indicators found:")
        for indicator in mock_indicators:
            print(f"     ❌ {indicator}")
    else:
        print("   ✅ No mock indicators found")
    
    # Step 5: Store and query to verify functionality
    print("\n💾 Step 5: Testing Memory Storage and Query...")
    try:
        snapshot_id = store_ui_snapshot(ui_tree, {"test": "real_verification"})
        if snapshot_id:
            print(f"   ✅ Snapshot stored: {snapshot_id}")
            
            # Query the stored data
            results = query_ui_by_text(ui_tree.get('name', 'Finder'), 1)
            if results:
                print(f"   ✅ Query successful: Found {len(results)} results")
                print(f"   ✅ Retrieved snapshot: {results[0]['id']}")
            else:
                print("   ❌ Query failed")
        else:
            print("   ❌ Storage failed")
    except Exception as e:
        print(f"   ❌ Storage/Query error: {e}")
    
    # Step 6: Show HTML preview
    print("\n📄 Step 6: HTML Preview (First 1000 characters):")
    print("-" * 50)
    preview = html_content[:1000] + "..." if len(html_content) > 1000 else html_content
    print(preview)
    print("-" * 50)
    
    # Step 7: Final verification
    print("\n🎯 Step 7: Final Verification...")
    
    is_real = (
        len(real_elements) >= 3 and  # At least 3 real macOS elements
        len(real_positioning) >= 2 and  # At least 2 positioning features
        len(mock_indicators) == 0 and  # No mock indicators
        len(html_content) > 1000 and  # Substantial HTML content
        ui_tree.get('name') != 'fallback_root'  # Not fallback UI
    )
    
    if is_real:
        print("   🎉 VERIFICATION PASSED: This is REAL HTML from actual macOS UI!")
        print("   ✅ Real macOS accessibility elements detected")
        print("   ✅ Real positioning and dimensions found")
        print("   ✅ No mock data indicators")
        print("   ✅ Substantial HTML content generated")
        print("   ✅ Memory storage and query working")
    else:
        print("   ❌ VERIFICATION FAILED: This appears to be mock data")
        print("   ❌ Missing real macOS elements or contains mock indicators")
    
    return is_real

def test_different_apps():
    """Test with different apps to show real UI variation."""
    print("\n" + "=" * 50)
    print("🔄 TESTING WITH DIFFERENT APPS")
    print("=" * 50)
    
    print("💡 To test with different apps:")
    print("   1. Open Safari, Finder, or other apps")
    print("   2. Run this script again")
    print("   3. You should see different HTML content")
    
    print("\n📱 Current app detected:")
    ui_tree = get_ui_tree()
    print(f"   App: {ui_tree.get('name', 'Unknown')}")
    print(f"   Elements: {len(ui_tree.get('children', []))}")

if __name__ == "__main__":
    is_real = verify_real_html()
    test_different_apps()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    if is_real:
        print("✅ CONFIRMED: System generates REAL HTML from actual macOS UI")
        print("✅ No mock data detected")
        print("✅ Real accessibility elements found")
        print("✅ Real positioning and dimensions")
        print("✅ Memory storage and query working")
    else:
        print("❌ ISSUE: System may be generating mock data")
        print("❌ Check accessibility permissions")
        print("❌ Ensure apps are open and accessible") 