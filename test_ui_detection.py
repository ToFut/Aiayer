#!/usr/bin/env python3
"""
Test UI Element Detection
Run the Total Screen Analyzer to see if it can detect the DO/Dismiss/Adjust buttons
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add sensors to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer/sensors')
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

async def test_ui_detection():
    """Test the Total Screen Analyzer UI detection"""
    try:
        from sensors.total_screen_analyzer import TotalScreenAnalyzer
        
        print("🔍 Testing Total Screen Analyzer for UI Element Detection")
        print("=" * 60)
        
        # Initialize analyzer
        analyzer = TotalScreenAnalyzer()
        
        print("📸 Capturing and analyzing current screen...")
        
        # Perform full screen analysis
        result = await analyzer.analyze_full_screen()
        
        if not result:
            print("❌ No analysis result returned")
            return
        
        print("✅ Analysis completed! Let's examine UI detection results...\n")
        
        # Extract UI analysis
        layers = result.get("layers", {})
        ui_analysis = layers.get("ui_analysis", {})
        text_analysis = layers.get("text_analysis", {})
        
        print("🔲 UI ELEMENTS DETECTED:")
        print("-" * 30)
        
        elements = ui_analysis.get("elements", [])
        if elements:
            for i, element in enumerate(elements, 1):
                element_type = element.get("type", "unknown")
                position = element.get("position", {})
                method = element.get("detection_method", "unknown")
                
                print(f"  {i}. Type: {element_type}")
                print(f"     Position: ({position.get('x', 0)}, {position.get('y', 0)}) - {position.get('width', 0)}x{position.get('height', 0)}")
                print(f"     Detection: {method}")
                print()
        else:
            print("  ❌ No UI elements detected")
        
        print(f"📊 SUMMARY:")
        print(f"  Total elements: {ui_analysis.get('total_count', 0)}")
        print(f"  Element types: {ui_analysis.get('element_types', {})}")
        
        # Check for buttons specifically
        print("\n🔘 BUTTON DETECTION:")
        print("-" * 20)
        
        button_elements = [e for e in elements if e.get("type") == "button"]
        interactive_elements = [e for e in elements if "interactive" in e.get("type", "")]
        
        print(f"  Buttons found: {len(button_elements)}")
        print(f"  Interactive elements: {len(interactive_elements)}")
        
        # Check text content for button text
        print("\n📝 TEXT CONTENT ANALYSIS:")
        print("-" * 25)
        
        all_text = text_analysis.get("all_text", "")
        if "DO" in all_text or "Dismiss" in all_text or "Adjust" in all_text:
            print("  ✅ Found button text in captured content:")
            lines = all_text.split('\n')
            for line in lines:
                if any(word in line for word in ['DO', 'Dismiss', 'Adjust', 'Button', 'Click']):
                    print(f"    \"{line.strip()}\"")
        else:
            print("  ❌ Button text not found in captured content")
            print(f"  📄 Sample content: {all_text[:300]}...")
        
        # Check categorized text
        categorized = text_analysis.get("categorized_text", {})
        ui_labels = categorized.get("ui_labels", [])
        
        print(f"\n🏷️  UI LABELS DETECTED: {len(ui_labels)}")
        for label in ui_labels[:10]:  # Show first 10
            print(f"    \"{label}\"")
        
        # Save results for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"ui_detection_test_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Full analysis saved to: {output_file}")
        
        # Specific button detection summary
        print("\n🎯 BUTTON DETECTION SUMMARY:")
        print("=" * 30)
        
        found_buttons = len(button_elements) > 0
        found_text = any(word in all_text for word in ['DO', 'Dismiss', 'Adjust'])
        found_ui_labels = len(ui_labels) > 0
        
        print(f"  Visual buttons detected: {'✅' if found_buttons else '❌'}")
        print(f"  Button text captured: {'✅' if found_text else '❌'}")
        print(f"  UI labels identified: {'✅' if found_ui_labels else '❌'}")
        
        if found_buttons or found_text or found_ui_labels:
            print("\n  🎉 SUCCESS: UI elements are being detected!")
        else:
            print("\n  ⚠️  ISSUE: UI elements not being properly detected")
            print("     This explains why your memory isn't capturing button details.")
        
    except Exception as e:
        print(f"❌ Error during UI detection test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ui_detection())