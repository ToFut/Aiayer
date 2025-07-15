#!/usr/bin/env python3
"""
Test script to see what macOS UI elements we can access
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_running_bundle_ids():
    """Return a set of bundle IDs for currently running apps (macOS only)."""
    import subprocess
    try:
        output = subprocess.check_output([
            'osascript',
            '-e', 'tell application "System Events" to get the bundle identifier of every process whose background only is false'
        ])
        bundle_ids = [b.strip() for b in output.decode().split(',') if b.strip()]
        return set(bundle_ids)
    except Exception as e:
        print(f"Could not get running bundle IDs: {e}")
        return set()

def test_macos_accessibility():
    """Test macOS accessibility access."""
    print("🔍 Testing macOS Accessibility Access")
    print("=" * 50)
    
    try:
        import atomacos
        print("✅ atomacos imported successfully")
        
        running_bundles = get_running_bundle_ids()
        # Always try getAppRefByPid(0), then only try bundle IDs for running apps
        methods = [
            ("getAppRefByPid(0)", lambda: atomacos.getAppRefByPid(0)),
        ]
        bundle_id_map = {
            'com.apple.finder': "Finder",
            'com.apple.Terminal': "Terminal",
            'com.apple.Safari': "Safari",
            'com.apple.systempreferences': "System Preferences",
        }
        for bundle_id, app_name in bundle_id_map.items():
            if bundle_id in running_bundles:
                methods.append((f"getAppRefByBundleId('{bundle_id}')", lambda b=bundle_id: atomacos.getAppRefByBundleId(b)))
        
        for method_name, method_func in methods:
            try:
                print(f"\n🔧 Testing: {method_name}")
                app = method_func()
                if app:
                    print(f"✅ Success: {method_name}")
                    
                    # Try to get basic properties
                    try:
                        role = getattr(app, 'AXRole', 'Unknown')
                        title = getattr(app, 'AXTitle', 'No Title')
                        print(f"   Role: {role}")
                        print(f"   Title: {title}")
                        
                        # Try to get children
                        try:
                            children = getattr(app, 'AXChildren', []) or []
                            print(f"   Children: {len(children)}")
                            
                            if children:
                                # Show first few children
                                for i, child in enumerate(children[:3]):
                                    try:
                                        child_role = getattr(child, 'AXRole', 'Unknown')
                                        child_title = getattr(child, 'AXTitle', 'No Title')
                                        print(f"     Child {i+1}: {child_role} - {child_title}")
                                    except Exception as e:
                                        print(f"     Child {i+1}: Error - {e}")
                                        
                        except Exception as e:
                            print(f"   Children Error: {e}")
                            
                    except Exception as e:
                        print(f"   Properties Error: {e}")
                        
                else:
                    print(f"❌ Failed: {method_name} - No app returned")
                    
            except Exception as e:
                print(f"❌ Error: {method_name} - {e}")
                
    except ImportError as e:
        print(f"❌ atomacos import failed: {e}")
        print("💡 Try: pip install atomacos")

def test_ui_scraper():
    """Test the UI scraper."""
    print("\n" + "="*50)
    print("🔧 Testing UI Scraper")
    print("="*50)
    
    try:
        from ui_scraper.base_scraper import get_ui_tree
        from html_mapper import ui_node_to_html
        
        ui_tree = get_ui_tree()
        print(f"✅ UI Tree extracted: {ui_tree.get('name', 'Unknown')}")
        print(f"✅ Elements: {len(ui_tree.get('children', []))}")
        
        html_content = ui_node_to_html(ui_tree)
        print(f"✅ HTML generated: {len(html_content)} characters")
        print(f"📄 HTML Preview:")
        print("-" * 40)
        print(html_content[:300] + "..." if len(html_content) > 300 else html_content)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ UI Scraper test failed: {e}")

def main():
    """Main function."""
    test_macos_accessibility()
    test_ui_scraper()
    
    print("\n" + "="*50)
    print("📋 Summary")
    print("="*50)
    print("If you see 'Unknown' elements, it means:")
    print("1. Accessibility permissions not granted")
    print("2. No accessible applications running")
    print("3. macOS security restrictions")
    print("\n💡 To fix:")
    print("1. Grant accessibility permissions to Terminal/IDE")
    print("2. Open some applications (Finder, Safari, etc.)")
    print("3. Check System Preferences > Security & Privacy > Privacy > Accessibility")

if __name__ == "__main__":
    main() 